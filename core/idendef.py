import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest

# ---------------------------------------------------------
# 1. VISUAL DEFECT DETECTION (Mocked YOLO / Mask R-CNN structure)
# ---------------------------------------------------------
class MockYOLOCNN(nn.Module):
    def __init__(self):
        super(MockYOLOCNN, self).__init__()
        # Expects a 3x224x224 RGB image (Standard for ResNet/YOLO backbones)
        self.conv1 = nn.Conv2d(3, 16, kernel_size=7, stride=2, padding=3)
        self.pool = nn.MaxPool2d(2, 2)
        # Simplified FC layer for simulation (16 channels * 56 * 56 spatial dims)
        self.fc = nn.Linear(16 * 56 * 56, 2)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class VisualDefectModel:
    def __init__(self):
        self.model = MockYOLOCNN()
        self.model.eval() 
        
    def detect(self, rgb_image_tensor):
        """
        Passes a synthetic image (1, 3, 224, 224) through the CNN.
        """
        with torch.no_grad():
            output = self.model(rgb_image_tensor)
            _, predicted = torch.max(output.data, 1)
            return predicted.item() == 1 # 1 = Defect

# ---------------------------------------------------------
# 2. VIBRATION ANOMALY DETECTION (Pretrained TCN-AutoEncoder)
# ---------------------------------------------------------
import os
from ml.tcn_ae import TCNAutoEncoder

class VibrationAnomalyModel:
    def __init__(self):
        self.models = {}
        self.thresholds = {}
        self._load_pretrained_models()
        
    def _load_pretrained_models(self):
        """Loads the individual TCN weights for all 16 machines."""
        pretrained_dir = os.path.join("models", "pretrained")
        
        # If they don't exist, we can't load them (warn the user)
        if not os.path.exists(pretrained_dir) or not os.listdir(pretrained_dir):
            print("[WARNING] Pretrained TCN models not found! Run train_vibration.py first.")
            return

        for filename in os.listdir(pretrained_dir):
            if filename.endswith(".pth"):
                machine_id = filename.replace(".pth", "")
                checkpoint = torch.load(os.path.join(pretrained_dir, filename), weights_only=True)
                
                model = TCNAutoEncoder(seq_len=500)
                model.load_state_dict(checkpoint['model_state_dict'])
                model.eval()
                
                self.models[machine_id] = model
                self.thresholds[machine_id] = checkpoint['anomaly_threshold']
                
    def detect(self, machine_id, vibration_time_series):
        """
        Takes 500 time-steps, computes reconstruction error, compares to machine's unique threshold.
        """
        if machine_id not in self.models:
            return False # Failsafe if not trained
            
        model = self.models[machine_id]
        threshold = self.thresholds[machine_id]
        
        # Convert to tensor (1, 1, 500)
        tensor_data = torch.tensor(vibration_time_series, dtype=torch.float32).view(1, 1, 500)
        
        with torch.no_grad():
            reconstruction = model(tensor_data)
            mse_loss = torch.mean((reconstruction - tensor_data)**2).item()
            
        # If reconstruction error > threshold, it's an anomaly!
        if mse_loss > threshold:
            print(f"[TCN ALERT] Machine {machine_id} Anomaly! Loss: {mse_loss:.4f} > {threshold:.4f}")
            return True
            
        return False

# ---------------------------------------------------------
# 3. PLC LOGIC CHECK (3D Spatial Coordinate + Time)
# ---------------------------------------------------------
class PLCLogicChecker:
    def __init__(self):
        self.spatial_tolerance_mm = 2.0 
        
    def detect(self, machine_id, expected_xyz, actual_xyz):
        e = np.array(expected_xyz)
        a = np.array(actual_xyz)
        distance_mm = np.linalg.norm(e - a)
        
        if distance_mm > self.spatial_tolerance_mm:
            print(f"[PLC ALARM] Machine {machine_id} 3D Deviation: {distance_mm:.2f}mm > {self.spatial_tolerance_mm}mm")
            return True
        return False

# ---------------------------------------------------------
# MASTER I-DENDEF ENGINE
# ---------------------------------------------------------
class IdendefEngine:
    def __init__(self):
        self.visual_model = VisualDefectModel()
        self.vibration_model = VibrationAnomalyModel()
        self.plc_logic = PLCLogicChecker()
        
    def evaluate_station(self, machine_id, rgb_tensor, vib_500, exp_xyz, act_xyz):
        defect_visual = self.visual_model.detect(rgb_tensor)
        defect_vib = self.vibration_model.detect(machine_id, vib_500)
        defect_plc = self.plc_logic.detect(machine_id, exp_xyz, act_xyz)
        
        is_defect = defect_visual or defect_vib or defect_plc
        
        reasons = []
        if defect_visual: reasons.append("Vision-YOLO")
        if defect_vib: reasons.append(f"TCN-{machine_id}")
        if defect_plc: reasons.append("PLC-3D-Dev")
            
        return is_defect, reasons
