import os
import json
import torch
import numpy as np
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

from ml.src.model import CycloneCNN
from ml.src.dataset import CycloneDataset, get_train_val_split

# --- config ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_CSV = os.path.join(PROJECT_ROOT, "data", "training_manifest.csv")
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, "ml", "checkpoints", "model.pt")

PREDICT_PATTERN = True

ID_TO_LABEL = {
    0: "eye",
    1: "banding",
    2: "curved_band",
    3: "shear_affected",
    4: "disorganized",
}

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def evaluate():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    dataset = CycloneDataset(
        manifest_csv_path=MANIFEST_CSV, 
        normalized_dir=NORMALIZED_DIR, 
        require_pattern_label=PREDICT_PATTERN
    )

    _, val_dataset = get_train_val_split(dataset)

    if len(val_dataset) == 0:
        print("Validation set is empty - nothing to evaluate.")
        return

    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False)

    model = CycloneCNN(
        num_classes=5,
        in_channels=2,
        predict_pattern=PREDICT_PATTERN, 
        predict_confidence=False
    ).to(device)
    
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"Checkpoint not found at {CHECKPOINT_PATH}. Train the model first.")
        return
        
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=device))
    model.eval()

    all_haversine_errors = []
    
    true_patterns = []
    pred_patterns = []

    with torch.no_grad():
        for images, targets in val_loader:
            images = images.to(device)
            true_centers = targets["center"].to(device)

            outputs = model(images)
            pred_centers = outputs["center"]

            # Calculate precise Haversine distance for each sample
            for i in range(images.size(0)):
                t_lat, t_lon = true_centers[i].cpu().numpy()
                p_lat, p_lon = pred_centers[i].cpu().numpy()
                err_km = haversine_km(t_lat, t_lon, p_lat, p_lon)
                all_haversine_errors.append(err_km)
                
            if PREDICT_PATTERN:
                t_pat = targets["pattern"].cpu().numpy()
                p_pat = torch.argmax(outputs["pattern"], dim=1).cpu().numpy()
                true_patterns.extend(t_pat)
                pred_patterns.extend(p_pat)

    num_samples = len(all_haversine_errors)
    avg_km_error = np.mean(all_haversine_errors)
    median_km_error = np.median(all_haversine_errors)
    max_km_error = np.max(all_haversine_errors)

    print("\n--- Evaluation Results ---")
    print(f"Validation samples evaluated: {num_samples}")
    print(f"Center-point MAE: {avg_km_error:.2f} km")
    print(f"Center-point Median Error: {median_km_error:.2f} km")
    print(f"Center-point Max Error: {max_km_error:.2f} km")
    
    metrics_export = {
        "samples": num_samples,
        "center_mae_km": float(avg_km_error),
        "center_median_km": float(median_km_error),
        "center_max_km": float(max_km_error),
    }

    if PREDICT_PATTERN:
        acc = accuracy_score(true_patterns, pred_patterns)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_patterns, pred_patterns, average=None, labels=list(range(5)), zero_division=0
        )
        cm = confusion_matrix(true_patterns, pred_patterns, labels=list(range(5)))
        
        print(f"\nPattern Classification Accuracy: {acc*100:.2f}%")
        print("Per-class F1 Scores:")
        per_class_f1 = {}
        for i, f in enumerate(f1):
            label_name = ID_TO_LABEL[i]
            print(f"  {label_name:>15}: {f:.2f}")
            per_class_f1[label_name] = float(f)
            
        metrics_export["pattern_accuracy"] = float(acc)
        metrics_export["pattern_f1_scores"] = per_class_f1
        metrics_export["confusion_matrix"] = cm.tolist()

    # Save metrics to JSON for backend/metrics usage
    metrics_path = os.path.join(PROJECT_ROOT, "ml", "configs", "evaluation_metrics.json")
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics_export, f, indent=2)
    print(f"\nSaved metrics to {metrics_path}")

if __name__ == "__main__":
    evaluate()