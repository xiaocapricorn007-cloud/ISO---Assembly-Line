import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest

# Vision Model Temporarily Disabled for Memory Optimization

# ---------------------------------------------------------
# 2. VIBRATION ANOMALY DETECTION (Pretrained TCN-AutoEncoder)
# ---------------------------------------------------------
import os
from ml.tcn_ae import TCNAutoEncoder

class VibrationAnomalyModel:
    def __init__(self):
        self.models = {}
        self.thresholds = {}
        self.base_freqs = {} # ADDED: to store the unique frequency per machine
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
                self.base_freqs[machine_id] = checkpoint.get('base_freq', 10.0) # Load base_freq
                
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
        self.vibration_model = VibrationAnomalyModel()
        self.plc_logic = PLCLogicChecker()
        
    def evaluate_station(self, machine_id, vib_500, exp_xyz, act_xyz):
        defect_vib = self.vibration_model.detect(machine_id, vib_500)
        defect_plc = self.plc_logic.detect(machine_id, exp_xyz, act_xyz)
        
        is_defect = defect_vib or defect_plc
        
        reasons = []
        if defect_vib: reasons.append(f"TCN-{machine_id}")
        if defect_plc: reasons.append("PLC-3D-Dev")
            
        return is_defect, reasons
