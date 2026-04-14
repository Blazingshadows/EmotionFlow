import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
import numpy as np
import argparse


# -------------------------------
# CONFIG
# -------------------------------
DATA_DIR = "YOLO_format"   # root folder for your dataset
MODEL_PATH = "checkpoints_affectnet_yolo/mobilenetv2_best.pth"
IMG_SIZE = 224
BATCH_SIZE = 32
NUM_CLASSES = 7   # we are ignoring "contempt"

EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


# -------------------------------
# DATASET (same as training, contempt ignored)
# -------------------------------
class AffectNetYOLOEval(Dataset):
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

        if self.transform:
            img = self.transform(img)

        return img, class_id


# -------------------------------
# DATALOADER
# -------------------------------
def get_val_loader():
    val_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    val_root = os.path.join(DATA_DIR, "valid")
    val_set = AffectNetYOLOEval(val_root, transform=val_tf)

    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE,
                            shuffle=False, num_workers=4)

    print("Validation samples:", len(val_set))
    return val_loader


# -------------------------------
# MODEL LOADING
# -------------------------------
def load_model(device, model_path=MODEL_PATH):
    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)
    state = torch.load(model_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


# -------------------------------
# EVALUATION
# -------------------------------
def evaluate(model_path=MODEL_PATH):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

    val_loader = get_val_loader()
    model = load_model(device, model_path=model_path)

    all_preds = []
    all_labels = []
    all_probs = []

    correct = 0
    total = 0

    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs, labels = imgs.to(device), labels.to(device)

            outputs = model(imgs)
            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(probs, 1)

            correct += (preds == labels).sum().item()
            total += labels.size(0)

            all_preds.extend(preds.cpu().numpy().tolist())
            all_labels.extend(labels.cpu().numpy().tolist())
            all_probs.extend(probs.cpu().numpy().tolist())

    overall_acc = correct / total
    print(f"\nOverall Validation Accuracy: {overall_acc:.4f}")

    # -------------------------------
    # Classification Report
    # -------------------------------
    print("\nClassification Report:")
    report = classification_report(
        all_labels, all_preds, target_names=EMOTIONS, digits=4
    )
    print(report)

    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="macro", zero_division=0
    )
    print(f"Macro Precision: {macro_precision:.4f}")
    print(f"Macro Recall:    {macro_recall:.4f}")
    print(f"Macro F1:        {macro_f1:.4f}")

    # Save report to file
    with open("affectnet_classification_report.txt", "w") as f:
        f.write(f"Overall Accuracy: {overall_acc:.4f}\n\n")
        f.write(f"Macro Precision: {macro_precision:.4f}\n")
        f.write(f"Macro Recall: {macro_recall:.4f}\n")
        f.write(f"Macro F1: {macro_f1:.4f}\n\n")
        f.write(report)
    print("Saved classification report to affectnet_classification_report.txt")

    # -------------------------------
    # Confusion Matrix
    # -------------------------------
    cm = confusion_matrix(all_labels, all_preds)
    print("\nConfusion Matrix:")
    print(cm)

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.tick_params(labelsize=11)

    ax.set(
        xticks=np.arange(len(EMOTIONS)),
        yticks=np.arange(len(EMOTIONS)),
        xticklabels=EMOTIONS,
        yticklabels=EMOTIONS,
        ylabel="True label",
        xlabel="Predicted label",
        title="AffectNet Validation Confusion Matrix (MobileNetV2)"
    )
    
    ax.title.set_fontsize(14)
    ax.title.set_fontweight('bold')
    ax.xaxis.label.set_fontsize(12)
    ax.yaxis.label.set_fontsize(12)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor", fontsize=11)
    plt.setp(ax.get_yticklabels(), fontsize=11)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=10
            )

    plt.tight_layout()
    plt.savefig("affectnet_confusion_matrix.png", dpi=300, bbox_inches='tight')
    print("Saved confusion matrix plot to affectnet_confusion_matrix.png")

    # -------------------------------
    # Per-Class Accuracy
    # -------------------------------
    per_class_acc = cm.diagonal() / cm.sum(axis=1)
    print("\nPer-class accuracy:")
    for label, acc in zip(EMOTIONS, per_class_acc):
        print(f"{label:9s}: {acc:.4f}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(EMOTIONS, per_class_acc, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'])
    ax.set_xlabel("Emotion", fontsize=12)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Per-Class Accuracy", fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.0)
    ax.grid(True, alpha=0.3, axis='y')
    
    for i, (bar, acc) in enumerate(zip(bars, per_class_acc)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{acc:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("per_class_accuracy.png", dpi=300, bbox_inches='tight')
    print("Saved per-class accuracy plot to per_class_accuracy.png")
    
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm_normalized, interpolation="nearest", cmap="YlOrRd")
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.tick_params(labelsize=11)
    
    ax.set(
        xticks=np.arange(len(EMOTIONS)),
        yticks=np.arange(len(EMOTIONS)),
        xticklabels=EMOTIONS,
        yticklabels=EMOTIONS,
        ylabel="True label",
        xlabel="Predicted label",
        title="Normalized Confusion Matrix (Row-wise)"
    )
    
    ax.title.set_fontsize(14)
    ax.title.set_fontweight('bold')
    ax.xaxis.label.set_fontsize(12)
    ax.yaxis.label.set_fontsize(12)
    
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor", fontsize=11)
    plt.setp(ax.get_yticklabels(), fontsize=11)
    
    thresh = cm_normalized.max() / 2.0
    for i in range(cm_normalized.shape[0]):
        for j in range(cm_normalized.shape[1]):
            ax.text(
                j, i, f"{cm_normalized[i, j]:.2f}",
                ha="center", va="center",
                color="white" if cm_normalized[i, j] > thresh else "black",
                fontsize=9
            )
    
    plt.tight_layout()
    plt.savefig("normalized_confusion_matrix.png", dpi=300, bbox_inches='tight')
    print("Saved normalized confusion matrix to normalized_confusion_matrix.png")

    # -------------------------------
    # Multi-class ROC-AUC (OvR)
    # -------------------------------
    y_true = label_binarize(all_labels, classes=list(range(NUM_CLASSES)))
    y_score = np.array(all_probs)

    try:
        macro_roc_auc = roc_auc_score(y_true, y_score, average="macro", multi_class="ovr")
        print(f"Macro ROC-AUC (OvR): {macro_roc_auc:.4f}")

        fig, ax = plt.subplots(figsize=(10, 8))
        for i, emotion in enumerate(EMOTIONS):
            fpr, tpr, _ = roc_curve(y_true[:, i], y_score[:, i])
            class_auc = roc_auc_score(y_true[:, i], y_score[:, i])
            ax.plot(fpr, tpr, linewidth=2, label=f"{emotion} (AUC={class_auc:.3f})")

        ax.plot([0, 1], [0, 1], "k--", linewidth=1)
        ax.set_xlabel("False Positive Rate", fontsize=12)
        ax.set_ylabel("True Positive Rate", fontsize=12)
        ax.set_title("Multi-class ROC Curves (One-vs-Rest)", fontsize=14, fontweight='bold')
        ax.legend(loc="lower right", fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("affectnet_roc_curves.png", dpi=300, bbox_inches='tight')
        print("Saved ROC curves to affectnet_roc_curves.png")
    except ValueError as e:
        print(f"Skipped ROC-AUC plot: {e}")
    
    plt.close('all')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AffectNet MobileNetV2 model")
    parser.add_argument("--model", default=MODEL_PATH, help="Path to model checkpoint (.pth)")
    args = parser.parse_args()
    evaluate(model_path=args.model)
