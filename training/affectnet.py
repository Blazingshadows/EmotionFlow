import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np


DATA_DIR = "YOLO_format"
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 50
LR = 1e-4
NUM_CLASSES = 7
MIXUP_ALPHA = 0.25
LABEL_SMOOTHING = 0.05

EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
class AffectNetYOLO(Dataset):
    def __init__(self, root, transform=None):
        self.root = root
        self.img_dir = os.path.join(root, "images")
        self.lbl_dir = os.path.join(root, "labels")
        self.transform = transform

        self.samples = []
        for lbl_file in os.listdir(self.lbl_dir):
            if lbl_file.endswith(".txt"):
                base_name = lbl_file.replace(".txt", "")
                img_id = None
                for ext in [".png", ".jpg", ".jpeg"]:
                    potential_img = base_name + ext
                    if os.path.exists(os.path.join(self.img_dir, potential_img)):
                        img_id = potential_img
                        break
                
                if img_id is None:
                    continue

                lbl_path = os.path.join(self.lbl_dir, lbl_file)
                with open(lbl_path, "r") as f:
                    first_line = f.readline().strip().split()
                    if not first_line:
                        continue
                    class_id = int(float(first_line[0]))

                if class_id == 7:
                    continue

                self.samples.append((img_id, class_id))

        self.class_counts = np.zeros(NUM_CLASSES, dtype=np.int64)
        for _, class_id in self.samples:
            if 0 <= class_id < NUM_CLASSES:
                self.class_counts[class_id] += 1

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_name, class_id = self.samples[idx]
        img_path = os.path.join(self.img_dir, img_name)

        img = Image.open(img_path).convert("RGB")

        if self.transform:
            img = self.transform(img)

        return img, class_id

    def get_class_counts(self):
        return self.class_counts.copy()


def build_weighted_sampler(train_set: AffectNetYOLO) -> WeightedRandomSampler:
    class_counts = train_set.get_class_counts().astype(np.float64)
    class_counts[class_counts == 0] = 1.0
    class_weights = 1.0 / class_counts
    sample_weights = np.array([class_weights[label] for _, label in train_set.samples], dtype=np.float64)
    return WeightedRandomSampler(
        weights=torch.from_numpy(sample_weights).double(),
        num_samples=len(sample_weights),
        replacement=True,
    )


def get_loaders():

    train_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.RandomResizedCrop(IMG_SIZE, scale=(0.85, 1.0)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    train_set = AffectNetYOLO(os.path.join(DATA_DIR, "train"), transform=train_tf)
    val_set   = AffectNetYOLO(os.path.join(DATA_DIR, "valid"), transform=val_tf)

    train_sampler = build_weighted_sampler(train_set)

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, sampler=train_sampler, num_workers=4)
    val_loader   = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    print("Train samples:", len(train_set))
    print("Valid samples:", len(val_set))
    print("Train class counts:", train_set.get_class_counts().tolist())

    return train_loader, val_loader, train_set


def build_model():
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)
    return model


def build_class_weights(train_set: AffectNetYOLO, device: torch.device) -> torch.Tensor:
    counts = train_set.get_class_counts().astype(np.float64)
    counts[counts == 0] = 1.0
    inv = 1.0 / counts
    normalized = inv / inv.sum() * len(inv)
    return torch.tensor(normalized, dtype=torch.float32, device=device)


def mixup_batch(inputs, targets, alpha=MIXUP_ALPHA):
    if alpha <= 0:
        return inputs, targets, targets, 1.0
    lam = float(np.random.beta(alpha, alpha))
    batch_size = inputs.size(0)
    index = torch.randperm(batch_size, device=inputs.device)
    mixed_x = lam * inputs + (1 - lam) * inputs[index, :]
    y_a, y_b = targets, targets[index]
    return mixed_x, y_a, y_b, lam


def compute_macro_f1_from_confusion(confusion: np.ndarray) -> float:
    per_class_f1 = []
    for i in range(confusion.shape[0]):
        tp = confusion[i, i]
        fp = confusion[:, i].sum() - tp
        fn = confusion[i, :].sum() - tp
        denom = (2 * tp) + fp + fn
        f1 = (2 * tp / denom) if denom > 0 else 0.0
        per_class_f1.append(f1)
    return float(np.mean(per_class_f1)) if per_class_f1 else 0.0


def train_model(model, train_loader, val_loader, train_set, device):

    class_weights = build_class_weights(train_set, device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=LABEL_SMOOTHING)
    optimizer = optim.AdamW(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_macro_f1 = 0
    os.makedirs("checkpoints_affectnet_yolo", exist_ok=True)

    history = {"train_acc": [], "val_acc": [], "val_macro_f1": [], "train_loss": []}

    print("\nTraining MobileNetV2 on Kaggle AffectNet YOLO...\n")

    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0
        correct = 0
        total = 0
        start = time.time()

        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)

            optimizer.zero_grad()

            mixed_imgs, targets_a, targets_b, lam = mixup_batch(imgs, labels)
            outputs = model(mixed_imgs)
            loss = lam * criterion(outputs, targets_a) + (1.0 - lam) * criterion(outputs, targets_b)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            epoch_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        train_acc = correct / total
        scheduler.step()

        model.eval()
        val_correct = 0
        val_total = 0
        confusion = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=np.int64)

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

                labels_np = labels.cpu().numpy()
                preds_np = preds.cpu().numpy()
                for t, p in zip(labels_np, preds_np):
                    confusion[int(t), int(p)] += 1

        val_acc = val_correct / val_total
        val_macro_f1 = compute_macro_f1_from_confusion(confusion)

        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)
        history["val_macro_f1"].append(val_macro_f1)
        history["train_loss"].append(epoch_loss)

        print(f"Epoch {epoch+1}/{EPOCHS} | "
              f"Loss: {epoch_loss:.4f} | "
              f"Train Acc: {train_acc:.4f} | "
              f"Val Acc: {val_acc:.4f} | "
              f"Val Macro-F1: {val_macro_f1:.4f} | "
              f"Time: {time.time() - start:.1f}s")

        if val_macro_f1 > best_macro_f1:
            best_macro_f1 = val_macro_f1
            torch.save(model.state_dict(), "checkpoints_affectnet_yolo/mobilenetv2_best.pth")
            print("✔ Best model saved (by Macro-F1)")

    print("\nTraining complete. Best Val Macro-F1 =", best_macro_f1)
    torch.save(model.state_dict(), "mobilenetv2_affectnet_yolo_final.pth")

    return history


def plot_training_history(history):
    epochs = range(1, len(history["train_acc"]) + 1)
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    axes[0].plot(epochs, history["train_acc"], 'b-', label="Train Accuracy", linewidth=2)
    axes[0].plot(epochs, history["val_acc"], 'r-', label="Validation Accuracy", linewidth=2)
    axes[0].set_xlabel("Epoch", fontsize=12)
    axes[0].set_ylabel("Accuracy", fontsize=12)
    axes[0].set_title("Model Accuracy Over Epochs", fontsize=14, fontweight='bold')
    axes[0].legend(fontsize=11)
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(epochs, history["train_loss"], 'g-', label="Train Loss", linewidth=2)
    axes[1].set_xlabel("Epoch", fontsize=12)
    axes[1].set_ylabel("Loss", fontsize=12)
    axes[1].set_title("Training Loss Over Epochs", fontsize=14, fontweight='bold')
    axes[1].legend(fontsize=11)
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(epochs, history["val_macro_f1"], 'm-', label="Val Macro-F1", linewidth=2)
    axes[2].set_xlabel("Epoch", fontsize=12)
    axes[2].set_ylabel("Macro-F1", fontsize=12)
    axes[2].set_title("Validation Macro-F1", fontsize=14, fontweight='bold')
    axes[2].legend(fontsize=11)
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("training_history.png", dpi=300, bbox_inches='tight')
    print("Saved training history plot to training_history.png")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(epochs, history["train_acc"], 'b-', marker='o', label="Train Accuracy", linewidth=2, markersize=4)
    ax.plot(epochs, history["val_acc"], 'r-', marker='s', label="Validation Accuracy", linewidth=2, markersize=4)
    ax.set_xlabel("Epoch", fontsize=12)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Training vs Validation Accuracy", fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("accuracy_comparison.png", dpi=300, bbox_inches='tight')
    print("Saved accuracy comparison plot to accuracy_comparison.png")
    plt.close('all')


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    train_loader, val_loader, train_set = get_loaders()
    model = build_model().to(device)
    
    history = train_model(model, train_loader, val_loader, train_set, device)
    plot_training_history(history)
