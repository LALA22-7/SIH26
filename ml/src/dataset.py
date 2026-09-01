import os
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, random_split
import numpy as np
import pandas as pd

# Fixed spatial size every frame gets resized to. Different .nc crops can
# come out at slightly different H,W depending on how the lat/lon bbox
# snaps to the source grid - DataLoader's default collate_fn calls
# torch.stack on a batch, which requires every tensor in that batch to be
# EXACTLY the same shape, so every image must be normalized to one size.
TARGET_SIZE = (256, 256)

# Single source of truth for the train/val split. train.py and evaluate.py
# BOTH import and call this - if they built the split separately (even with
# "the same" fraction), there'd be no guarantee they landed on the same
# rows, and evaluate.py could silently score the model on data it was
# actually trained on. Fixed seed makes the split reproducible across
# separate script runs/processes (unlike relying on whatever the global
# RNG state happens to be, which train.py's original version did).
VAL_FRACTION = 0.15
SPLIT_SEED = 42


def get_train_val_split(dataset):
    val_size = max(1, int(VAL_FRACTION * len(dataset)))
    train_size = len(dataset) - val_size
    generator = torch.Generator().manual_seed(SPLIT_SEED)
    return random_split(dataset, [train_size, val_size], generator=generator)


class CycloneDataset(Dataset):
    """
    Reads rows from training_manifest.csv (written by validate_and_join.py)
    and loads the matching .npz frame (written by standardize_data.py).

    IMPORTANT: each .npz already contains a normalized [2, H, W] tensor
    under the key "image" (channel 0 = IR, channel 1 = water vapour).
    There is no separate ir_path / wv_path in the manifest - the old
    version of this file was written against a schema that never
    actually existed in the pipeline's output.
    """

    def __init__(self, manifest_csv_path, normalized_dir, require_pattern_label=False):
        df = pd.read_csv(manifest_csv_path)

        # Keep only rows that actually have a matched ground-truth position.
        # validate_and_join.py leaves center_lat/center_lon as "" (empty
        # string) when a frame had no ground-truth match within its 90-min
        # tolerance window - you can't train a regression target on those.
        df = df[df["center_lat"].notna() & (df["center_lat"] != "")]
        df = df[df["center_lon"].notna() & (df["center_lon"] != "")]

        # pattern_label is "unlabeled" for EVERY row until you wire in a
        # separate taxonomy-labeling step (validate_and_join.py says this
        # explicitly in its own printed summary). Only filter/require it
        # once you actually have real labels, otherwise this drops every
        # row and the dataset ends up empty.
        if require_pattern_label:
            df = df[df["pattern_label"] != "unlabeled"]

        if len(df) == 0:
            raise ValueError(
                "No usable rows in manifest after filtering. If you just set "
                "require_pattern_label=True, check whether pattern_label is "
                "still 'unlabeled' for every row - that's expected until "
                "classification labels are joined in separately."
            )

        self.manifest = df.reset_index(drop=True)
        self.normalized_dir = normalized_dir
        self.require_pattern_label = require_pattern_label

        if require_pattern_label:
            labels = sorted(self.manifest["pattern_label"].unique())
            self.label_to_id = {label: i for i, label in enumerate(labels)}

    def __len__(self):
        return len(self.manifest)

    def _npz_path(self, row):
        # standardize_data.py writes frames to:
        #   data/normalized/<event_id>/frames/<event_id>_<timestamp>.npz
        # the training manifest only kept the basename (file_id), so the
        # full path has to be rebuilt the same way standardize_data.py
        # originally built it.
        return os.path.join(self.normalized_dir, row["event_id"], "frames", row["file_id"])

    def __getitem__(self, idx):
        row = self.manifest.iloc[idx]
        npz_path = self._npz_path(row)

        data = np.load(npz_path)
        image_np = data["image"]  # already [2, H, W], already 0-1 normalized - don't re-normalize

        image_tensor = torch.tensor(image_np, dtype=torch.float32)

        # Resize to a fixed uniform spatial shape so batch stacking succeeds.
        # NOTE: this only resizes the image - center_lat/center_lon are real
        # geographic coordinates (degrees), not pixel coordinates, so they
        # do NOT need any corresponding adjustment here.
        image_tensor = image_tensor.unsqueeze(0)  # [1, 2, H, W]
        image_tensor = F.interpolate(
            image_tensor, size=TARGET_SIZE, mode="bilinear", align_corners=False
        )
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