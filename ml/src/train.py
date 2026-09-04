"""
ml/src/train.py
───────────────
Training loop for CycloneCNN.

Current config: centre regression + pattern classification, 100 epochs.
Pattern labels come from scripts/label_frames.py (IBTrACS intensity rules).

Class weights fix the 70% "disorganized" imbalance — without them the model
learns to predict "disorganized" for everything and gets ~70% accuracy while
being completely useless for rarer classes (eye, shear_affected).
"""
import os
import collections

import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.src.model import CycloneTemporalModel
from ml.src.dataset import CycloneDataset, get_train_val_split

# ── Config ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_CSV   = os.path.join(PROJECT_ROOT, "data", "training_manifest.csv")
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, "ml", "checkpoints", "model.pt")

NUM_EPOCHS    = 200
BATCH_SIZE    = 8       # larger batch = more stable gradients; AdaptiveAvgPool handles variable H/W
LEARNING_RATE = 0.001

PREDICT_PATTERN = True  # requires scripts/label_frames.py to have been run first

# Loss weights — centre MSE and pattern CE are on different scales.
# Tuned so neither dominates: typical centre MSE ~0.01-0.1, CE ~1.0-2.0
CENTER_LOSS_WEIGHT  = 10.0   # up-weight centre to keep it from being swamped by CE
PATTERN_LOSS_WEIGHT = 1.0


def _compute_class_weights(dataset) -> torch.Tensor:
    """
    Inverse-frequency class weights to counteract label imbalance.

    With 70% disorganized and 2.5% shear_affected, plain CE loss learns to
    always predict disorganized. Inverse-freq weights force the model to pay
    attention to minority classes (eye, shear_affected, curved_band).
    """
    label_counts: dict[int, int] = collections.Counter()
    for i in range(len(dataset)):
        _, targets = dataset[i]
        if "pattern" in targets:
            label_counts[int(targets["pattern"].item())] += 1

    num_classes = 5
    total = sum(label_counts.values())
    weights = []
    for c in range(num_classes):
        count = label_counts.get(c, 1)          # avoid div-by-zero
        weights.append(total / (num_classes * count))
    w = torch.tensor(weights, dtype=torch.float32)
    print("  Class weights:", {i: f"{w[i]:.2f}" for i in range(num_classes)})
    return w


def run_training() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)
    print("Checkpoint will be saved to:", CHECKPOINT_PATH)
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)

    full_dataset = CycloneDataset(
        manifest_csv_path=MANIFEST_CSV,
        normalized_dir=NORMALIZED_DIR,
        require_pattern_label=PREDICT_PATTERN,
    )
    print(f"Dataset: {len(full_dataset)} usable frames")

    train_dataset, val_dataset = get_train_val_split(full_dataset)
    print(f"  Train: {len(train_dataset)}   Val: {len(val_dataset)}")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  drop_last=False)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, drop_last=False)

    model = CycloneTemporalModel(
        num_classes=5,
        in_channels=2,
    ).to(device)

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    # Reduce LR by 0.5 if val loss plateaus for 10 epochs — prevents stagnation
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=10, verbose=True
    )

    mse_loss = nn.MSELoss()

    # Class-weighted cross-entropy — critical for the imbalanced label distribution
    class_weights = _compute_class_weights(train_dataset).to(device)
    ce_loss = nn.CrossEntropyLoss(weight=class_weights)

    best_val_loss = float("inf")
    best_epoch    = 0

    for epoch in range(NUM_EPOCHS):
        # ── Training ──────────────────────────────────────────────────────
        model.train()
        running_loss = 0.0

        for images, targets in train_loader:
            images      = images.to(device).unsqueeze(1)  # Add T=1 dimension: [B, 1, C, H, W]
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

        # ── Validation ────────────────────────────────────────────────────
        model.eval()
        val_running_loss  = 0.0
        val_centre_errors = []   # km errors for readable progress

        with torch.no_grad():
            for images, targets in val_loader:
                images       = images.to(device).unsqueeze(1)
                true_centers = targets["center"].to(device)
                outputs      = model(images)

                c_loss = mse_loss(outputs["center"], true_centers) * CENTER_LOSS_WEIGHT
                p_loss = torch.tensor(0.0, device=device)
                if PREDICT_PATTERN:
                    true_patterns = targets["pattern"].to(device)
                    p_loss = ce_loss(outputs["pattern"], true_patterns) * PATTERN_LOSS_WEIGHT

                val_running_loss += (c_loss + p_loss).item()

                # Approximate km error (cos-corrected, good enough for logging)
                lat_r = torch.deg2rad(true_centers[:, 0])
                lat_err_km = (outputs["center"][:, 0] - true_centers[:, 0]) * 111.0
                lon_err_km = (outputs["center"][:, 1] - true_centers[:, 1]) * 111.0 * torch.cos(lat_r)
                dist_km    = torch.sqrt(lat_err_km ** 2 + lon_err_km ** 2)
                val_centre_errors.extend(dist_km.cpu().tolist())

        val_loss   = val_running_loss / len(val_loader)
        val_mae_km = sum(val_centre_errors) / len(val_centre_errors) if val_centre_errors else 0.0

        scheduler.step(val_loss)

        # Save best checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch    = epoch + 1
            torch.save(model.state_dict(), CHECKPOINT_PATH)

        # Print every 5 epochs + first + last
        if (epoch + 1) % 5 == 0 or epoch == 0 or epoch == NUM_EPOCHS - 1:
            print(
                f"Epoch [{epoch+1:>3}/{NUM_EPOCHS}] "
                f"train={train_loss:.4f}  val={val_loss:.4f}  "
                f"centre_mae={val_mae_km:.1f}km  "
                f"best_epoch={best_epoch}"
            )

    print(f"\nTraining complete.")
    print(f"Best checkpoint: epoch {best_epoch}, val_loss={best_val_loss:.4f}")
    print(f"Saved to: {CHECKPOINT_PATH}")


if __name__ == "__main__":
    run_training()
