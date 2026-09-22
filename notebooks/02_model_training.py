"""
SIH26 Model Training — Kaggle Kernel (GPU)
============================================
Trains the CycloneCNN / CycloneTemporalModel on the existing 7-cyclone
dataset (423 frames) using Kaggle's free T4 GPU.

REQUIRED KAGGLE DATASETS (attach these in kernel-metadata.json):
  1. lala227/sih26-cyclone-data   → contains data/normalized/ and data/training_manifest.csv
  2. lala227/sih26-ml-codebase    → contains ml/src/{model.py, dataset.py, train.py, ...}

The script adapts all file paths to Kaggle's /kaggle/input/ mount points
and saves checkpoints to /kaggle/working/ for download.
"""
import os
import sys
import shutil
import collections
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
import pandas as pd

# ── Kaggle environment detection ──────────────────────────────────────────────
ON_KAGGLE = os.path.exists("/kaggle/working")

if ON_KAGGLE:
    # On Kaggle, datasets are mounted read-only at /kaggle/input/<dataset-slug>/
    ML_CODEBASE = Path("/kaggle/input/sih26-ml-codebase")
    DATA_ROOT   = Path("/kaggle/input/sih26-cyclone-data")
    CHECKPOINT_DIR = Path("/kaggle/working/checkpoints")
else:
    # Local fallback for testing
    PROJECT_ROOT = Path(__file__).parent.parent
    ML_CODEBASE = PROJECT_ROOT / "ml"
    DATA_ROOT   = PROJECT_ROOT / "data"
    CHECKPOINT_DIR = PROJECT_ROOT / "ml" / "checkpoints"

CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# ── Paths ─────────────────────────────────────────────────────────────────────
MANIFEST_CSV   = DATA_ROOT / "training_manifest.csv"
NORMALIZED_DIR = DATA_ROOT / "normalized"
CHECKPOINT_PATH = CHECKPOINT_DIR / "model.pt"

# ── Hyperparameters ───────────────────────────────────────────────────────────
NUM_EPOCHS          = 100
BATCH_SIZE          = 8
LEARNING_RATE       = 0.001
PREDICT_PATTERN     = True
CENTER_LOSS_WEIGHT  = 10.0
PATTERN_LOSS_WEIGHT = 1.0
VAL_FRACTION        = 0.15
SPLIT_SEED          = 42
TARGET_SIZE         = (256, 256)


# ══════════════════════════════════════════════════════════════════════════════
# MODEL (inlined from ml/src/model.py to avoid import path issues on Kaggle)
# ══════════════════════════════════════════════════════════════════════════════

class CycloneCNN(nn.Module):
    def __init__(self, num_classes=5, in_channels=2, predict_pattern=True, predict_confidence=True):
        super(CycloneCNN, self).__init__()
        self.predict_pattern = predict_pattern
        self.predict_confidence = predict_confidence

        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )

        self.pool = nn.AdaptiveAvgPool2d((16, 16))
        self.fc_shared = nn.Linear(32 * 16 * 16, 128)
        self.fc_center = nn.Linear(128, 2)

        if predict_pattern:
            self.fc_pattern = nn.Linear(128, num_classes)
        if predict_confidence:
            self.fc_confidence = nn.Linear(128, 1)

    def forward_features(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc_shared(x))
        return x

    def forward(self, x):
        x = self.forward_features(x)
        out = {"center": self.fc_center(x)}
        if self.predict_pattern:
            out["pattern"] = self.fc_pattern(x)
        if self.predict_confidence:
            out["confidence"] = torch.sigmoid(self.fc_confidence(x))
        return out


class CycloneTemporalModel(nn.Module):
    def __init__(self, num_classes=5, in_channels=2, hidden_dim=128, num_layers=1):
        super(CycloneTemporalModel, self).__init__()
        self.cnn = CycloneCNN(num_classes, in_channels, predict_pattern=True, predict_confidence=True)
        self.gru = nn.GRU(input_size=128, hidden_size=hidden_dim, num_layers=num_layers, batch_first=True)
        self.fc_t12 = nn.Linear(hidden_dim, 2)
        self.fc_t24 = nn.Linear(hidden_dim, 2)
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, x):
        B, T, C, H, W = x.size()
        x_flat = x.view(B * T, C, H, W)
        cnn_features = self.cnn.forward_features(x_flat)

        out_center = self.cnn.fc_center(cnn_features).view(B, T, 2)
        out_pattern = self.cnn.fc_pattern(cnn_features).view(B, T, -1)

        raw_conf = self.cnn.fc_confidence(cnn_features)
        scaled_conf = torch.sigmoid(raw_conf / self.temperature)
        out_confidence = scaled_conf.view(B, T, 1)

        gru_input = cnn_features.view(B, T, -1)
        gru_out, _ = self.gru(gru_input)

        t12_center = self.fc_t12(gru_out)
        t24_center = self.fc_t24(gru_out)

        out = {
            "center":     out_center[:, -1, :],
            "pattern":    out_pattern[:, -1, :],
            "confidence": out_confidence[:, -1, :],
            "t12_center": t12_center[:, -1, :],
            "t24_center": t24_center[:, -1, :],
        }
        return out


# ══════════════════════════════════════════════════════════════════════════════
# DATASET (inlined from ml/src/dataset.py)
# ══════════════════════════════════════════════════════════════════════════════

class CycloneDataset(Dataset):
    def __init__(self, manifest_csv_path, normalized_dir, require_pattern_label=False):
        df = pd.read_csv(manifest_csv_path)

        df = df[df["center_lat"].notna() & (df["center_lat"] != "")]
        df = df[df["center_lon"].notna() & (df["center_lon"] != "")]

        if require_pattern_label:
            df = df[df["pattern_label"] != "unlabeled"]

        if len(df) == 0:
            raise ValueError(
                "No usable rows in manifest after filtering. Check pattern_label column."
            )

        self.manifest = df.reset_index(drop=True)
        self.normalized_dir = str(normalized_dir)
        self.require_pattern_label = require_pattern_label

        if require_pattern_label:
            self.label_to_id = {
                "eye": 0, "banding": 1, "curved_band": 2,
                "shear_affected": 3, "disorganized": 4,
            }

    def __len__(self):
        return len(self.manifest)

    def _npz_path(self, row):
        return os.path.join(self.normalized_dir, row["event_id"], "frames", row["file_id"])

    def __getitem__(self, idx):
        row = self.manifest.iloc[idx]
        npz_path = self._npz_path(row)

        data = np.load(npz_path)
        image_np = data["image"]  # [2, H, W], already 0-1 normalized

        image_tensor = torch.tensor(image_np, dtype=torch.float32)
        image_tensor = image_tensor.unsqueeze(0)
        image_tensor = F.interpolate(image_tensor, size=TARGET_SIZE, mode="bilinear", align_corners=False)
        image_tensor = image_tensor.squeeze(0)  # [2, 256, 256]

        target = {
            "center": torch.tensor(
                [float(row["center_lat"]), float(row["center_lon"])],
                dtype=torch.float32,
            )
        }

        if self.require_pattern_label:
            target["pattern"] = torch.tensor(
                self.label_to_id[row["pattern_label"]], dtype=torch.long
            )

        return image_tensor, target


def get_train_val_split(dataset):
    val_size = max(1, int(VAL_FRACTION * len(dataset)))
    train_size = len(dataset) - val_size
    generator = torch.Generator().manual_seed(SPLIT_SEED)
    return random_split(dataset, [train_size, val_size], generator=generator)


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING LOOP
# ══════════════════════════════════════════════════════════════════════════════

def compute_class_weights(dataset):
    label_counts = collections.Counter()
    for i in range(len(dataset)):
        _, targets = dataset[i]
        if "pattern" in targets:
            label_counts[int(targets["pattern"].item())] += 1

    num_classes = 5
    total = sum(label_counts.values())
    weights = []
    for c in range(num_classes):
        count = label_counts.get(c, 1)
        weights.append(total / (num_classes * count))
    w = torch.tensor(weights, dtype=torch.float32)
    print("  Class weights:", {i: f"{w[i]:.2f}" for i in range(num_classes)})
    return w


def run_training():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"SIH26 CYCLONEWATCH — MODEL TRAINING")
    print(f"{'='*60}")
    print(f"Device:          {device}")
    if device.type == "cuda":
        print(f"GPU:             {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory:      {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
    print(f"Manifest:        {MANIFEST_CSV}")
    print(f"Normalized dir:  {NORMALIZED_DIR}")
    print(f"Checkpoint path: {CHECKPOINT_PATH}")
    print(f"Epochs:          {NUM_EPOCHS}")
    print(f"Batch size:      {BATCH_SIZE}")
    print()

    # Verify data exists
    if not MANIFEST_CSV.exists():
        print(f"❌ ERROR: Manifest CSV not found at {MANIFEST_CSV}")
        print("   Make sure the sih26-cyclone-data dataset is attached to this kernel.")
        print(f"   Contents of {DATA_ROOT}:")
        if DATA_ROOT.exists():
            for item in DATA_ROOT.iterdir():
                print(f"     {item.name}")
        return
    
    if not NORMALIZED_DIR.exists():
        print(f"❌ ERROR: Normalized data dir not found at {NORMALIZED_DIR}")
        return

    # Load dataset
    full_dataset = CycloneDataset(
        manifest_csv_path=str(MANIFEST_CSV),
        normalized_dir=str(NORMALIZED_DIR),
        require_pattern_label=PREDICT_PATTERN,
    )
    print(f"Dataset: {len(full_dataset)} usable frames")

    train_dataset, val_dataset = get_train_val_split(full_dataset)
    print(f"  Train: {len(train_dataset)}   Val: {len(val_dataset)}")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  drop_last=False)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, drop_last=False)

    # Build model
    model = CycloneTemporalModel(
        num_classes=5,
        in_channels=2,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Model parameters: {total_params:,}")

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=10, verbose=False
    )

    mse_loss = nn.MSELoss()
    class_weights = compute_class_weights(train_dataset).to(device)
    ce_loss = nn.CrossEntropyLoss(weight=class_weights)

    best_val_loss = float("inf")
    best_epoch = 0

    print(f"\n{'─'*60}")
    print(f"{'Epoch':>6} {'Train Loss':>12} {'Val Loss':>12} {'MAE (km)':>10} {'Best':>6}")
    print(f"{'─'*60}")

    for epoch in range(NUM_EPOCHS):
        # ── Training ──
        model.train()
        running_loss = 0.0

        for images, targets in train_loader:
            images = images.to(device).unsqueeze(1)  # [B, 1, C, H, W]
            true_centers = targets["center"].to(device)

            optimizer.zero_grad()
            outputs = model(images)

            loss = mse_loss(outputs["center"], true_centers) * CENTER_LOSS_WEIGHT

            if PREDICT_PATTERN:
                true_patterns = targets["pattern"].to(device)
                loss = loss + ce_loss(outputs["pattern"], true_patterns) * PATTERN_LOSS_WEIGHT

            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        train_loss = running_loss / len(train_loader)

        # ── Validation ──
        model.eval()
        val_running_loss = 0.0
        val_centre_errors = []

        with torch.no_grad():
            for images, targets in val_loader:
                images = images.to(device).unsqueeze(1)
                true_centers = targets["center"].to(device)
                outputs = model(images)

                c_loss = mse_loss(outputs["center"], true_centers) * CENTER_LOSS_WEIGHT
                p_loss = torch.tensor(0.0, device=device)
                if PREDICT_PATTERN:
                    true_patterns = targets["pattern"].to(device)
                    p_loss = ce_loss(outputs["pattern"], true_patterns) * PATTERN_LOSS_WEIGHT

                val_running_loss += (c_loss + p_loss).item()

                lat_r = torch.deg2rad(true_centers[:, 0])
                lat_err_km = (outputs["center"][:, 0] - true_centers[:, 0]) * 111.0
                lon_err_km = (outputs["center"][:, 1] - true_centers[:, 1]) * 111.0 * torch.cos(lat_r)
                dist_km = torch.sqrt(lat_err_km ** 2 + lon_err_km ** 2)
                val_centre_errors.extend(dist_km.cpu().tolist())

        val_loss = val_running_loss / len(val_loader)
        val_mae_km = sum(val_centre_errors) / len(val_centre_errors) if val_centre_errors else 0.0

        scheduler.step(val_loss)

        # Save best checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch + 1
            torch.save(model.state_dict(), str(CHECKPOINT_PATH))

        # Print every 5 epochs + first + last
        if (epoch + 1) % 5 == 0 or epoch == 0 or epoch == NUM_EPOCHS - 1:
            print(
                f"{epoch+1:>6} {train_loss:>12.4f} {val_loss:>12.4f} "
                f"{val_mae_km:>10.1f} {best_epoch:>6}"
            )

    print(f"{'─'*60}")
    print(f"\n✅ Training complete!")
    print(f"   Best checkpoint: epoch {best_epoch}, val_loss={best_val_loss:.4f}")
    print(f"   Saved to: {CHECKPOINT_PATH}")
    print(f"   File size: {CHECKPOINT_PATH.stat().st_size / 1e6:.2f} MB")
    
    if ON_KAGGLE:
        print(f"\n📥 Download your model from the 'Output' tab of this kernel.")


if __name__ == "__main__":
    run_training()
