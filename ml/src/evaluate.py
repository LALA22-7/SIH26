import os
import math
import torch
from torch.utils.data import DataLoader
from ml.src.model import CycloneCNN
from ml.src.dataset import CycloneDataset, get_train_val_split

# --- config ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_CSV = os.path.join(PROJECT_ROOT, "data", "training_manifest.csv")
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, "model.pt")

KM_PER_DEGREE_LAT = 111.0  # ~constant everywhere on Earth


def evaluate():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # NOTE: manifest_csv_path, not manifest_csv - matches CycloneDataset's
    # actual constructor signature in dataset.py.
    dataset = CycloneDataset(manifest_csv_path=MANIFEST_CSV, normalized_dir=NORMALIZED_DIR)

    # Uses the SAME seeded split train.py used (get_train_val_split lives
    # in dataset.py and is imported by both scripts) - this is what
    # guarantees val_dataset here is actually the rows the model never
    # trained on, instead of an independently-randomized, non-matching
    # subset that could overlap with training data.
    _, val_dataset = get_train_val_split(dataset)

    if len(val_dataset) == 0:
        print("Validation set is empty - nothing to evaluate.")
        return

    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False)

    model = CycloneCNN(predict_pattern=False, predict_confidence=False).to(device)
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"Checkpoint not found at {CHECKPOINT_PATH}. Train the model first.")
        return
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=device))
    model.eval()

    total_km_error = 0.0
    num_samples = 0

    with torch.no_grad():
        for images, targets in val_loader:
            images = images.to(device)
            true_centers = targets["center"].to(device)  # [B, 2] -> (lat, lon)

            outputs = model(images)
            pred_centers = outputs["center"]

            lat_diff_deg = pred_centers[:, 0] - true_centers[:, 0]
            lon_diff_deg = pred_centers[:, 1] - true_centers[:, 1]

            # Longitude degrees shrink toward the poles - one degree of
            # longitude covers cos(latitude) times as much ground distance
            # as one degree of latitude does. Latitude degrees don't need
            # this correction; longitude does. Use the TRUE latitude
            # (not predicted) as the reference point for the conversion.
            lat_rad = torch.deg2rad(true_centers[:, 0])
            km_per_degree_lon = KM_PER_DEGREE_LAT * torch.cos(lat_rad)

            lat_error_km = lat_diff_deg * KM_PER_DEGREE_LAT
            lon_error_km = lon_diff_deg * km_per_degree_lon

            # Actual point-to-point distance per sample (flat-earth
            # approximation, fine at this scale/precision), not two
            # separately-averaged axis errors that could partially cancel
            # out and understate the true typical miss distance.
            dist_km = torch.sqrt(lat_error_km ** 2 + lon_error_km ** 2)

            total_km_error += dist_km.sum().item()
            num_samples += images.size(0)

    avg_km_error = total_km_error / num_samples

    print("\n--- Evaluation Results ---")
    print(f"Validation samples evaluated: {num_samples}")
    print(f"Average center-point error: {avg_km_error:.2f} km")


if __name__ == "__main__":
    evaluate()