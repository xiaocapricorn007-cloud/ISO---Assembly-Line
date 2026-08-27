import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest

# ---------------------------------------------------------
# 1. VISUAL DEFECT DETECTION (PyTorch CNN)
# ---------------------------------------------------------
class DummyVisionCNN(nn.Module):
    def __init__(self):
        super(DummyVisionCNN, self).__init__()
        # Extremely simplified CNN for synthetic data
        self.conv1 = nn.Conv2d(1, 4, kernel_size=3, padding=1)
        self.fc = nn.Linear(4 * 28 * 28, 2) # Binary classification: Normal vs Defect

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class VisualDefectModel:
    def __init__(self):
        self.model = DummyVisionCNN()
        self.model.eval() # Set to inference mode
        
    def detect(self, synthetic_image_tensor):
        """
        Passes a synthetic image (1, 1, 28, 28) through the CNN.
        Returns True if a defect is visually identified.
        """
        with torch.no_grad():
            output = self.model(synthetic_image_tensor)
            _, predicted = torch.max(output.data, 1)
            # Let's say class 1 is defect, class 0 is normal
            return predicted.item() == 1

# ---------------------------------------------------------
# 2. VIBRATION ANOMALY DETECTION (Time-Series ML)
# ---------------------------------------------------------
class VibrationAnomalyModel:
    def __init__(self):
        # We use an Isolation Forest trained on synthetic vibration time-series data
        self.model = IsolationForest(contamination=0.01, random_state=42)
        self._train_synthetic()
        
    def _train_synthetic(self):
        # Generate synthetic 'normal' vibration signatures (e.g., sine waves + noise)
        normal_data = []
        for _ in range(1000):
            t = np.linspace(0, 1, 10) # 10 time steps per cycle
            vib = np.sin(2 * np.pi * 5 * t) + np.random.normal(0, 0.1, 10)
            normal_data.append(vib)
        self.model.fit(normal_data)
        
    def detect(self, vibration_time_series):
        """
        Takes an array of recent vibration readings (length 10).
        Returns True if the pattern is anomalous compared to baseline.
        """
        X = np.array(vibration_time_series).reshape(1, -1)
        pred = self.model.predict(X)
        return pred[0] == -1 # -1 indicates anomaly

# ---------------------------------------------------------
# 3. PLC LOGIC CHECK (Deterministic Logic Loop)
# ---------------------------------------------------------
class PLCLogicChecker:
    def __init__(self):
        pass
        
    def detect(self, expected_position, actual_position, tolerance=0.05):
        """
        Checks if the robot/machine is physically where it should be.
        Returns True if position is out of bounds (defect/error).
        """
        deviation = abs(expected_position - actual_position)
        if deviation > tolerance:
            print(f"[PLC ALARM] Position mismatch! Expected {expected_position}, Actual {actual_position}")
            return True
        return False

# ---------------------------------------------------------
# MASTER I-DENDEF ENGINE
# ---------------------------------------------------------
class IdendefEngine:
    """
    I-DENDEF: Predictive Quality Guard
    Aggregates the 3 defect detection streams.
    """
    def __init__(self):
        self.visual_model = VisualDefectModel()
        self.vibration_model = VibrationAnomalyModel()
        self.plc_logic = PLCLogicChecker()
        
    def evaluate_station(self, image_tensor, vibration_array, expected_pos, actual_pos):
        """
        Runs all three checks. If ANY fail, returns a Defect Flag.
        """
        defect_visual = self.visual_model.detect(image_tensor)
        defect_vib = self.vibration_model.detect(vibration_array)
        defect_plc = self.plc_logic.detect(expected_pos, actual_pos)
        
        is_defect = defect_visual or defect_vib or defect_plc
        
        reasons = []
        if defect_visual: reasons.append("VisualCNN")
        if defect_vib: reasons.append("VibrationAnomaly")
        if defect_plc: reasons.append("PLCLogic")
            
        return is_defect, reasons
