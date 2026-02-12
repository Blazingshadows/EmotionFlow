import torch
import torch.nn as nn
import torch.nn.functional as F


class DepthwiseSeparableConv(nn.Module):
    """
    Depthwise + Pointwise convolution block.
    """
    def __init__(self, in_channels, out_channels):
        super().__init__()

        # Depthwise convolution
        self.depthwise = nn.Conv2d(
            in_channels,
            in_channels,
            kernel_size=3,
            padding=1,
            groups=in_channels,  # Key part — groups = in_channels
            bias=False
        )

        # Pointwise convolution
        self.pointwise = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=1,
            bias=False
        )

        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out = self.depthwise(x)
        out = self.pointwise(out)
        out = self.bn(out)
        out = self.relu(out)
        return out


class MiniXception(nn.Module):
    """
    Mini-Xception model for FER2013-style 48x48 grayscale emotion recognition.
    Light, fast, and ideal for real-time inference.
    """

    def __init__(self, num_classes=7):
        super().__init__()

        # Entry flow
        self.entry = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True)
        )

        # Depthwise separable blocks (increasing channels)
        self.block1 = DepthwiseSeparableConv(32, 64)
        self.block2 = DepthwiseSeparableConv(64, 128)
        self.block3 = DepthwiseSeparableConv(128, 256)

        # Global pool + classifier
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        # Input: (batch, 1, 48, 48)
        x = self.entry(x)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.pool(x)               # -> (batch, 256, 1, 1)
        x = x.view(x.size(0), -1)      # -> (batch, 256)
        x = self.fc(x)                 # -> (batch, num_classes)
        return x
