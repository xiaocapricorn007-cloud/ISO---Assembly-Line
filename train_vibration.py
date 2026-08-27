import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from ml.tcn_ae import TCNAutoEncoder

# Define the exact machine topologies required
MACHINE_TOPOLOGY = {
    'Station_A': 3,
    'Station_B': 2,
    'Station_C_Dark': 5,
    'Station_D': 4,
    'Station_E': 2
}

def generate_synthetic_dataset(base_freq, num_samples=1000, seq_len=500):
    """Generates a distinct vibration dataset for a specific machine."""
    t = np.linspace(0, 2, seq_len)
    data = []
    for _ in range(num_samples):
        # Base frequency + Harmonics + Unique Gaussian Noise
        vib = (np.sin(2 * np.pi * base_freq * t) + 
               0.5 * np.sin(2 * np.pi * (base_freq * 2.5) * t) + 
               np.random.normal(0, 0.15, seq_len))
        data.append(vib)
    
    # Convert to PyTorch tensors (Batch, Channels, SeqLen)
    tensor_data = torch.tensor(np.array(data), dtype=torch.float32).unsqueeze(1)
    return tensor_data

def train_machine_model(machine_id, base_freq):
    print(f"--- Training TCN-AutoEncoder for Machine: {machine_id} ---")
    
    # 1. Generate distinct data
    train_data = generate_synthetic_dataset(base_freq)
    
    # 2. Init Model & Optimizer
    model = TCNAutoEncoder(seq_len=500)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # 3. Fast Training Loop (15 epochs for mock synthetic convergence)
    model.train()
    for epoch in range(15):
        optimizer.zero_grad()
        output = model(train_data)
        loss = criterion(output, train_data)
        loss.backward()
        optimizer.step()
        
        if epoch % 5 == 0:
            print(f"Epoch {epoch} | Loss: {loss.item():.4f}")
            
    # 4. Calculate threshold (max loss on training data + buffer)
    model.eval()
    with torch.no_grad():
        reconstructions = model(train_data)
        losses = torch.mean((reconstructions - train_data)**2, dim=2) # MSE per sample
        threshold = losses.max().item() * 1.5 # 50% buffer for anomaly threshold
        
    print(f"[OK] Trained {machine_id}. Anomaly Threshold Set: {threshold:.4f}\n")
    
    # 5. Save Model and Threshold
    save_path = os.path.join("models", "pretrained", f"{machine_id}.pth")
    torch.save({
        'model_state_dict': model.state_dict(),
        'anomaly_threshold': threshold,
        'base_freq': base_freq
    }, save_path)

def main():
    print("Starting Pre-Training Pipeline for I-DENDEF TCN-AutoEncoders...\n")
    
    base_freq_counter = 10.0 # Start at 10Hz, increment for uniqueness
    
    for station, count in MACHINE_TOPOLOGY.items():
        for i in range(1, count + 1):
            machine_id = f"{station}_M{i}"
            # Give each machine a slightly different unique frequency profile
            base_freq_counter += 2.5 
            train_machine_model(machine_id, base_freq_counter)
            
    print("🎉 All 16 Machine models successfully pretrained and saved to models/pretrained/")

if __name__ == "__main__":
    main()
