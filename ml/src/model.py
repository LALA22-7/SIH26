import torch
import torch.nn as nn

class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size, bias=True):
        super(ConvLSTMCell, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size[0] // 2, kernel_size[1] // 2
        self.bias = bias
        self.conv = nn.Conv2d(in_channels=self.input_dim + self.hidden_dim,
                              out_channels=4 * self.hidden_dim,
                              kernel_size=self.kernel_size,
                              padding=self.padding,
                              bias=self.bias)

    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv(combined)
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

    def init_hidden(self, batch_size, image_size):
        height, width = image_size
        return (torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device),
                torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device))


class CycloneCNN(nn.Module):
    def __init__(self, num_classes=5, in_channels=2):
        super(CycloneCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 16, 3, 1, 1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, 1, 1), nn.ReLU(), nn.MaxPool2d(2),
        )

    def forward(self, x):
        return self.features(x)


class CycloneTemporalModel(nn.Module):
    def __init__(self, num_classes=5, in_channels=2, hidden_dim=64):
        super(CycloneTemporalModel, self).__init__()
        self.cnn = CycloneCNN(num_classes, in_channels)
        self.convlstm = ConvLSTMCell(input_dim=32, hidden_dim=hidden_dim, kernel_size=(3, 3), bias=True)
        self.pool = nn.AdaptiveAvgPool2d((4, 4))
        self.fc_shared = nn.Linear(hidden_dim * 16, 128)
        
        self.fc_center = nn.Linear(128, 2)
        self.fc_pattern = nn.Linear(128, num_classes)
        self.fc_confidence = nn.Linear(128, 1)
        
        self.fc_t12 = nn.Linear(128, 2)
        self.fc_t24 = nn.Linear(128, 2)
        
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, x):
        B, T, C, H, W = x.size()
        f_seq = []
        for t in range(T):
            f_seq.append(self.cnn(x[:, t, :, :, :]))
            
        spatial_size = f_seq[0].size()[2:]
        h, c = self.convlstm.init_hidden(B, spatial_size)
        
        for t in range(T):
            h, c = self.convlstm(f_seq[t], (h, c))
            
        pooled = self.pool(h).view(B, -1)
        shared = torch.relu(self.fc_shared(pooled))
        
        out = {
            "center": self.fc_center(shared),
            "pattern": self.fc_pattern(shared),
            "confidence": torch.sigmoid(self.fc_confidence(shared) / self.temperature),
            "t12_center": self.fc_t12(shared),
            "t24_center": self.fc_t24(shared),
        }
        
        return out