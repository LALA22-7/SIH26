import os
import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import DataLoader
from ml.src.model import CycloneCNN
from ml.src.dataset import CycloneDataset, get_train_val_split

# --- config ---
# --- config ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_CSV = os.path.join(PROJECT_ROOT, "data", "training_manifest.csv")
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, "model.pt")

NUM_EPOCHS = 20
BATCH_SIZE = 4
LEARNING_RATE = 0.001

# pattern_label is "unlabeled" for every row until you wire in a separate
# classification-labeling step - keep this False until that exists, then
# flip it to True here AND pass require_pattern_label=True to the dataset.
PREDICT_PATTERN = False

# lat/lon MSE and classification cross-entropy live on very different
# scales - weight them if one starts dominating the gradient.
CENTER_LOSS_WEIGHT = 1.0
PATTERN_LOSS_WEIGHT = 1.0


def run_training():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    # NOTE: model, optimizer, and losses are created BEFORE the training
    # loop uses them. In the original file they were created AFTER the
    # loop, which meant model.train() ran on a name that didn't exist yet
    # in that scope - Python raised UnboundLocalError before any real
    # training code could run at all.
    full_dataset = CycloneDataset(
        manifest_csv_path=MANIFEST_CSV,
        normalized_dir=NORMALIZED_DIR,
        require_pattern_label=PREDICT_PATTERN,
    )

    # Fixed, seeded split shared with evaluate.py (see get_train_val_split
    # in dataset.py) - this used to be an unseeded inline random_split,
    # which meant a separate evaluation script could never reliably
    # reconstruct the same held-out rows.
    train_dataset, val_dataset = get_train_val_split(full_dataset)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = CycloneCNN(
        num_classes=5, predict_pattern=PREDICT_PATTERN, predict_confidence=False
    ).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    mse_loss = nn.MSELoss()
    ce_loss = nn.CrossEntropyLoss()

    for epoch in range(NUM_EPOCHS):
        model.train()
        running_loss = 0.0

        for images, targets in train_loader:
            images = images.to(device)
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

        # --- validation ---
        model.eval()
        val_running_loss = 0.0
        with torch.no_grad():
            for images, targets in val_loader:
                images = images.to(device)
                true_centers = targets["center"].to(device)
                outputs = model(images)
                loss = mse_loss(outputs["center"], true_centers) * CENTER_LOSS_WEIGHT
                if PREDICT_PATTERN:
                    true_patterns = targets["pattern"].to(device)
                    loss = loss + ce_loss(outputs["pattern"], true_patterns) * PATTERN_LOSS_WEIGHT
                val_running_loss += loss.item()
        val_loss = val_running_loss / len(val_loader)

        print(f"Epoch [{epoch+1}/{NUM_EPOCHS}] train_loss={train_loss:.4f} val_loss={val_loss:.4f}")

    torch.save(model.state_dict(), CHECKPOINT_PATH)
    print(f"Training complete! Model saved to {CHECKPOINT_PATH}")


if __name__ == "__main__":
    run_training()