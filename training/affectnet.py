import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import matplotlib.pyplot as plt


DATA_DIR = "YOLO_format"
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 50
LR = 1e-4
NUM_CLASSES = 7

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

                self.samples.append(img_id)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_name = self.samples[idx]
        img_path = os.path.join(self.img_dir, img_name)
        
        base_name = os.path.splitext(img_name)[0]
        lbl_path = os.path.join(self.lbl_dir, base_name + ".txt")

        img = Image.open(img_path).convert("RGB")

        with open(lbl_path, "r") as f:
            first_line = f.readline().strip().split()
            class_id = int(float(first_line[0]))

        if class_id > 7:
            class_id -= 1

        if self.transform:
            img = self.transform(img)

        return img, class_id


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

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
    val_loader   = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    print("Train samples:", len(train_set))
    print("Valid samples:", len(val_set))

    return train_loader, val_loader


def build_model():
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)
    return model


def train_model(model, train_loader, val_loader, device):

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_acc = 0
    os.makedirs("checkpoints_affectnet_yolo", exist_ok=True)

    history = {"train_acc": [], "val_acc": [], "train_loss": []}

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
            outputs = model(imgs)
            loss = criterion(outputs, labels)

            loss.backward()
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

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_acc = val_correct / val_total

        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)
        history["train_loss"].append(epoch_loss)

        print(f"Epoch {epoch+1}/{EPOCHS} | "
              f"Loss: {epoch_loss:.4f} | "
              f"Train Acc: {train_acc:.4f} | "
              f"Val Acc: {val_acc:.4f} | "
              f"Time: {time.time() - start:.1f}s")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), "checkpoints_affectnet_yolo/mobilenetv2_best.pth")
            print("✔ Best model saved")

    print("\nTraining complete. Best Val Accuracy =", best_acc)
    torch.save(model.state_dict(), "mobilenetv2_affectnet_yolo_final.pth")

    return history


def plot_training_history(history):
    epochs = range(1, len(history["train_acc"]) + 1)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
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
    
    train_loader, val_loader = get_loaders()
    model = build_model().to(device)
    
    history = train_model(model, train_loader, val_loader, device)
    plot_training_history(history)
