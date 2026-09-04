import torch
import torch.nn as nn

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
        x = x.view(x.size(0), -1)  # flatten
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
        
        # Temperature parameter for confidence calibration
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, x):
        """
        x shape: [B, T, C, H, W]
        """
        B, T, C, H, W = x.size()
        
        # Reshape to process all frames through CNN
        x_flat = x.view(B * T, C, H, W)
        cnn_features = self.cnn.forward_features(x_flat)
        
        # Apply standard CNN heads to get Current Center, Pattern, and Confidence
        out_center = self.cnn.fc_center(cnn_features).view(B, T, 2)
        out_pattern = self.cnn.fc_pattern(cnn_features).view(B, T, -1)
        
        # Temperature scaled confidence
        raw_conf = self.cnn.fc_confidence(cnn_features)
        scaled_conf = torch.sigmoid(raw_conf / self.temperature)
        out_confidence = scaled_conf.view(B, T, 1)
        
        # Sequence modeling with GRU
        gru_input = cnn_features.view(B, T, -1)
        gru_out, _ = self.gru(gru_input)
        
        # Predict future centers
        t12_center = self.fc_t12(gru_out)
        t24_center = self.fc_t24(gru_out)
        
        # Get predictions for the last timestep
        out = {
            "center": out_center[:, -1, :],
            "pattern": out_pattern[:, -1, :],
            "confidence": out_confidence[:, -1, :],
            "t12_center": t12_center[:, -1, :],
            "t24_center": t24_center[:, -1, :]
        }
        
        return out