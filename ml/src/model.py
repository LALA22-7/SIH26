import torch
import torch.nn as nn


class CycloneCNN(nn.Module):
    def __init__(self, num_classes=5, in_channels=2, predict_pattern=True, predict_confidence=True):
        """
        in_channels=2: your data is IR + water vapour stacked as [2, H, W].
        The old version hardcoded Conv2d(3, ...), which would crash on the
        very first forward pass since your tensors only ever have 2 channels.

        predict_pattern / predict_confidence let you turn heads on or off
        depending on what you're actually training for at a given stage
        (e.g. keep predict_pattern=False until real pattern labels exist).
        """
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

        # AdaptiveAvgPool2d forces the feature map down to a fixed 16x16
        # no matter what H,W your real bbox crop produces (it will NOT be
        # a clean 64x64 - that was a guess in the original code, not a
        # measured value). This makes fc_shared's input size correct
        # regardless of the actual crop resolution.
        self.pool = nn.AdaptiveAvgPool2d((16, 16))
        self.fc_shared = nn.Linear(32 * 16 * 16, 128)

        # Output head 1: continuous coordinates (lat, lon)
        self.fc_center = nn.Linear(128, 2)

        # Output head 2: pattern classification (only if you're using it)
        if predict_pattern:
            self.fc_pattern = nn.Linear(128, num_classes)

        # Output head 3: confidence score (only if you're using it -
        # inference.py used to call this without the model ever producing it)
        if predict_confidence:
            self.fc_confidence = nn.Linear(128, 1)

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = x.view(x.size(0), -1)  # flatten
        x = torch.relu(self.fc_shared(x))

        out = {"center": self.fc_center(x)}

        if self.predict_pattern:
            out["pattern"] = self.fc_pattern(x)

        if self.predict_confidence:
            out["confidence"] = torch.sigmoid(self.fc_confidence(x))

        return out