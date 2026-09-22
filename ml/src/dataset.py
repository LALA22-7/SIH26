import os
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, random_split
import numpy as np
import pandas as pd

TARGET_SIZE = (256, 256)
VAL_FRACTION = 0.15
SPLIT_SEED = 42

def get_train_val_split(dataset):
    val_size = max(1, int(VAL_FRACTION * len(dataset)))
    train_size = len(dataset) - val_size
    generator = torch.Generator().manual_seed(SPLIT_SEED)
    return random_split(dataset, [train_size, val_size], generator=generator)


class CycloneDataset(Dataset):
    LABEL_MAP = {"eye": 0, "banding": 1, "curved_band": 2, "shear_affected": 3, "disorganized": 4}
    
    def __init__(self, manifest_csv_path, normalized_dir, require_pattern_label=False, seq_len=4):
        df = pd.read_csv(manifest_csv_path)

        df = df[df["center_lat"].notna() & (df["center_lat"] != "")]
        df = df[df["center_lon"].notna() & (df["center_lon"] != "")]

        if require_pattern_label:
            df = df[df["pattern_label"] != "unlabeled"]

        if len(df) == 0:
            raise ValueError("No usable rows in manifest after filtering.")

        if "timestamp" in df.columns:
            df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values(by=["event_id", "timestamp_dt"]).reset_index(drop=True)
        else:
            # Fallback for manifests lacking timestamp column
            df = df.sort_values(by=["event_id", "file_id"]).reset_index(drop=True)

        self.normalized_dir = str(normalized_dir)
        self.require_pattern_label = require_pattern_label
        self.seq_len = seq_len
        self.sequences = []
        
        for event_id, group in df.groupby("event_id"):
            if len(group) >= self.seq_len:
                for i in range(len(group) - self.seq_len + 1):
                    self.sequences.append(group.iloc[i:i+self.seq_len])

    def __len__(self): 
        return len(self.sequences)

    def __getitem__(self, idx):
        seq_df = self.sequences[idx]
        imgs = []
        for _, row in seq_df.iterrows():
            path = os.path.join(self.normalized_dir, row["event_id"], "frames", row["file_id"])
            arr = np.load(path)["image"]
            img = torch.tensor(arr, dtype=torch.float32).unsqueeze(0)
            img = F.interpolate(img, size=TARGET_SIZE, mode="bilinear", align_corners=False).squeeze(0)
            imgs.append(img)
            
        last_row = seq_df.iloc[-1]
        
        target = {
            "center": torch.tensor([float(last_row["center_lat"]), float(last_row["center_lon"])], dtype=torch.float32)
        }
        
        if self.require_pattern_label:
            target["pattern"] = torch.tensor(self.LABEL_MAP[last_row["pattern_label"]], dtype=torch.long)
            
        return torch.stack(imgs, dim=0), target