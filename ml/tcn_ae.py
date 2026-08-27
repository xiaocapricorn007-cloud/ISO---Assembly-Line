import torch
import torch.nn as nn

class TCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, dilation):
        super().__init__()
        # 1D Convolution with dilation
        self.conv = nn.Conv1d(
            in_channels, out_channels, kernel_size,
            padding=(kernel_size - 1) * dilation,
            dilation=dilation
        )
        self.relu = nn.ReLU()

    def forward(self, x):
        # Crop the padding from the right to maintain sequence length
        out = self.conv(x)
        return self.relu(out[:, :, :-self.conv.padding[0]])

class TCNAutoEncoder(nn.Module):
    """
    Temporal Convolutional Network (TCN) Combined with an AutoEncoder.
    Learns to reconstruct normal machine vibration sequences.
    """
    def __init__(self, seq_len=500):
        super().__init__()
        # ENCODER (TCN)
        self.enc1 = TCNBlock(in_channels=1, out_channels=16, kernel_size=3, dilation=1)
        self.enc2 = TCNBlock(in_channels=16, out_channels=8, kernel_size=3, dilation=2)
        # Compress sequence from 500 -> 125
        self.pool = nn.AdaptiveAvgPool1d(125)
        
        # DECODER
        self.dec1 = nn.ConvTranspose1d(8, 16, kernel_size=4, stride=2, padding=1) # 125 -> 250
        self.dec2 = nn.ConvTranspose1d(16, 1, kernel_size=4, stride=2, padding=1) # 250 -> 500

    def forward(self, x):
        # x shape: (batch_size, 1, 500)
        e = self.enc1(x)
        e = self.enc2(e)
        latent = self.pool(e)
        
        d = torch.relu(self.dec1(latent))
        reconstructed = self.dec2(d)
        return reconstructed
