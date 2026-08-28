import torch
import torch.nn as nn
from ml.tcn_ae import TCNBlock

class PLC_TCNAutoEncoder(nn.Module):
    """
    TCN AutoEncoder for 3D PLC trajectories (X, Y, Z).
    Handles variable sequence lengths (must be multiple of 4).
    """
    def __init__(self, seq_len):
        super().__init__()
        assert seq_len % 4 == 0, "seq_len must be a multiple of 4"
        
        # ENCODER
        self.enc1 = TCNBlock(in_channels=3, out_channels=16, kernel_size=3, dilation=1)
        self.enc2 = TCNBlock(in_channels=16, out_channels=8, kernel_size=3, dilation=2)
        
        latent_size = seq_len // 4
        self.pool = nn.AdaptiveAvgPool1d(latent_size)
        
        # DECODER
        self.dec1 = nn.ConvTranspose1d(8, 16, kernel_size=4, stride=2, padding=1)
        self.dec2 = nn.ConvTranspose1d(16, 3, kernel_size=4, stride=2, padding=1)

    def forward(self, x):
        # x shape: (batch_size, 3, seq_len)
        e = self.enc1(x)
        e = self.enc2(e)
        latent = self.pool(e)
        
        d = torch.relu(self.dec1(latent))
        reconstructed = self.dec2(d)
        return reconstructed
