import os
import time
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import cv2
import numpy as np

# Handle both direct execution and package import
try:
    from .minixception_model import MiniXception
except ImportError:
    from minixception_model import MiniXception


# -------------------------
# Dataset Loader
# -------------------------
EMOTIONS = ["Angry","Disgust","Fear","Happy","Sad","Surprise","Neutral"]

class FER2013Dataset(Dataset):
    def __init__(self, root):
        self.samples = []

        for idx, emotion in enumerate(EMOTIONS):
            # Try lowercase first, then original case
            folder = os.path.join(root, emotion.lower())
            if not os.path.exists(folder):
                folder = os.path.join(root, emotion)
            if not os.path.exists(folder):
                print(f"⚠ Warning: Emotion folder '{emotion}' not found at {os.path.join(root, emotion.lower())}")
                continue

            try:
                for file in os.listdir(folder):
                    if file.lower().endswith((".jpg", ".png", ".jpeg")):
                        self.samples.append((os.path.join(folder, file), idx))
            except Exception as e:
                print(f"Error loading from {folder}: {e}")
        
        if len(self.samples) == 0:
            print(f"⚠ ERROR: No images found in {root}!")
            print(f"   Expected structure: {root}/{EMOTIONS[0].lower()}/*.jpg")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        path, label = self.samples[index]

        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (48, 48))

        img = img.astype("float32") / 255.0
        img = torch.tensor(img).unsqueeze(0)

        return img, torch.tensor(label)


# -------------------------
# Training Function
# -------------------------
def train(model, train_loader, val_loader, device, epochs=100, checkpoint_dir=None):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, 
                                                           patience=5)

    best_val_acc = 0
    if checkpoint_dir is None:
        checkpoint_dir = "checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)

    print("\nStarting training...\n")

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        correct = 0
        total = 0

        start_time = time.time()

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
        train_time = time.time() - start_time

        # -------------------------
        # Validation
        # -------------------------
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

        print(f"Epoch {epoch+1}/{epochs} | "
              f"Loss: {epoch_loss:.4f} | "
              f"Train Acc: {train_acc:.4f} | "
              f"Val Acc: {val_acc:.4f} | "
              f"Time: {train_time:.1f}s")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_path = os.path.join(checkpoint_dir, "minixception_best.pth")
            torch.save(model.state_dict(), best_model_path)
            print(f"✔ Saved new best model to {best_model_path}")
        
        scheduler.step(val_acc)

    print("\nTraining complete!")
    print(f"Best Validation Accuracy: {best_val_acc:.4f}")


# -------------------------
# Main Script
# -------------------------
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}\n")

    # Get absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    train_path = os.path.join(project_root, "FER2013", "train")
    test_path = os.path.join(project_root, "FER2013", "test")
    checkpoint_dir = os.path.join(project_root, "checkpoints")
    
    print(f"Loading datasets from:")
    print(f"  Train: {train_path}")
    print(f"  Test:  {test_path}\n")

    # Load datasets
    train_dataset = FER2013Dataset(train_path)
    val_dataset   = FER2013Dataset(test_path)

    # Check if datasets are empty
    if len(train_dataset) == 0:
        print("ERROR: Training dataset is empty!")
        print(f"Please ensure {train_path} contains subdirectories: angry, disgust, fear, happy, neutral, sad, surprise")
        print("Each subdirectory should contain .jpg or .png files")
        sys.exit(1)
    
    print(f"✓ Loaded {len(train_dataset)} training images")
    
    if len(val_dataset) == 0:
        print(f"⚠ Validation dataset is empty! Using 20% of training data for validation.")
        train_size = int(0.8 * len(train_dataset))
        val_size = len(train_dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(train_dataset, [train_size, val_size])
        print(f"✓ Split into {len(train_dataset)} train and {len(val_dataset)} validation images")
    else:
        print(f"✓ Loaded {len(val_dataset)} validation images")

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_dataset,   batch_size=64, shuffle=False, num_workers=0)

    # Build model
    model = MiniXception().to(device)
    print(f"✓ MiniXception model created\n")

    # Train
    train(model, train_loader, val_loader, device, epochs=100, checkpoint_dir=checkpoint_dir)

    # Save final model
    final_model_path = os.path.join(project_root, "assets", "minixception_torch.pth")
    os.makedirs(os.path.dirname(final_model_path), exist_ok=True)
    torch.save(model.state_dict(), final_model_path)
    print(f"\n✓ Saved final model to {final_model_path}")
