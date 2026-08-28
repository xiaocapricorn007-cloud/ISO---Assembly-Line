import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from ml.tcn_ae_plc import PLC_TCNAutoEncoder

MACHINE_TOPOLOGY = {
    'Station_A': 3,
    'Station_B': 2,
    'Station_C_Dark': 5,
    'Station_D': 4,
    'Station_E': 2
}

def generate_robotic_kinematics(L1, L2, seq_len):
    """Simulates a 2-DOF planar + 1-DOF Z-axis robotic arm."""
    t = np.linspace(0, 1, seq_len)
    
    # Angles sweeping over time
    theta1 = np.pi * np.sin(2 * np.pi * t) # Base rotation
    theta2 = 0.5 * np.pi * np.cos(4 * np.pi * t) # Shoulder/Elbow
    
    # Forward Kinematics
    x = L1 * np.cos(theta1) + L2 * np.cos(theta1 + theta2)
    y = L1 * np.sin(theta1) + L2 * np.sin(theta1 + theta2)
    z = 100.0 + 50.0 * np.sin(2 * np.pi * t) # Z variation
    
    return x, y, z

def generate_plc_dataset(L1, L2, num_samples=1000, seq_len=400):
    data = []
    for _ in range(num_samples):
        x, y, z = generate_robotic_kinematics(L1, L2, seq_len)
        # Add slight variations per sample
        x += np.random.normal(0, 1.0, seq_len)
        y += np.random.normal(0, 1.0, seq_len)
        z += np.random.normal(0, 1.0, seq_len)
        
        # Stack channels: (3, seq_len)
        trajectory = np.vstack((x, y, z))
        data.append(trajectory)
        
    tensor_data = torch.tensor(np.array(data), dtype=torch.float32)
    return tensor_data

def train_plc_model(machine_id, L1, L2, seq_len):
    print(f"--- Training PLC TCN for Machine: {machine_id} | seq_len: {seq_len} ---")
    train_data = generate_plc_dataset(L1, L2, seq_len=seq_len)
    
    model = PLC_TCNAutoEncoder(seq_len=seq_len)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    model.train()
    for epoch in range(15):
        optimizer.zero_grad()
        output = model(train_data)
        loss = criterion(output, train_data)
        loss.backward()
        optimizer.step()
        if epoch % 5 == 0:
            print(f"Epoch {epoch} | Loss: {loss.item():.4f}")
            
    model.eval()
    with torch.no_grad():
        reconstructions = model(train_data)
        losses = torch.mean((reconstructions - train_data)**2, dim=(1, 2)) 
        threshold = losses.max().item() * 1.5 
        
    print(f"[OK] Trained {machine_id}. Anomaly Threshold Set: {threshold:.4f}\n")
    
    os.makedirs(os.path.join("models", "pretrained_plc"), exist_ok=True)
    save_path = os.path.join("models", "pretrained_plc", f"{machine_id}.pth")
    torch.save({
        'model_state_dict': model.state_dict(),
        'anomaly_threshold': threshold,
        'seq_len': seq_len,
        'L1': L1,
        'L2': L2
    }, save_path)

def main():
    print("Starting Pre-Training Pipeline for PLC TCN-AutoEncoders...\n")
    
    base_L1 = 150.0
    base_L2 = 100.0
    seq_len = 200
    
    for station, count in MACHINE_TOPOLOGY.items():
        for i in range(1, count + 1):
            machine_id = f"{station}_M{i}"
            train_plc_model(machine_id, base_L1, base_L2, seq_len)
            base_L1 += 5.0
            base_L2 += 2.0
            seq_len += 20 # Must remain multiple of 4
            
    print("🎉 All 16 PLC models successfully pretrained and saved to models/pretrained_plc/")

if __name__ == "__main__":
    main()
