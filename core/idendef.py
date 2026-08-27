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
# 2. VIBRATION ANOMALY DETECTION (FFT + Isolation Forest)
# ---------------------------------------------------------
class VibrationAnomalyModel:
    def __init__(self):
        # Increased contamination as we have tighter thresholds now
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self._train_synthetic_fft()
        
    def _train_synthetic_fft(self):
        """Trains on the Frequency Domain (FFT) of 500-step windows."""
        fft_data = []
        for _ in range(1000):
            t = np.linspace(0, 2, 500) # 2 seconds, 500 samples (250Hz)
            # Base frequencies + noise
            vib = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 50 * t) + np.random.normal(0, 0.2, 500)
            
            # Compute FFT (Magnitude)
            fft_mag = np.abs(np.fft.fft(vib))[:250] # Take positive frequencies
            fft_data.append(fft_mag)
            
        self.model.fit(fft_data)
        
    def detect(self, vibration_time_series):
        """
        Takes 500 time-steps, converts to FFT, and predicts anomaly.
        """
        # Ensure 500 length
        vib_array = np.array(vibration_time_series)
        fft_mag = np.abs(np.fft.fft(vib_array))[:250].reshape(1, -1)
        
        pred = self.model.predict(fft_mag)
        return pred[0] == -1

# ---------------------------------------------------------
# 3. PLC LOGIC CHECK (3D Spatial Coordinate + Time)
# ---------------------------------------------------------
class PLCLogicChecker:
    def __init__(self):
        self.spatial_tolerance_mm = 2.0 
        
    def detect(self, expected_xyz, actual_xyz):
        """
        Checks 3D Euclidean distance between expected and actual robotic arm positions.
        xyz tuples: (x, y, z)
        """
        e = np.array(expected_xyz)
        a = np.array(actual_xyz)
        
        distance_mm = np.linalg.norm(e - a)
        
        if distance_mm > self.spatial_tolerance_mm:
            print(f"[PLC ALARM] 3D Deviation: {distance_mm:.2f}mm > {self.spatial_tolerance_mm}mm Tolerance!")
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
        
    def evaluate_station(self, rgb_tensor, vib_500, exp_xyz, act_xyz):
        defect_visual = self.visual_model.detect(rgb_tensor)
        defect_vib = self.vibration_model.detect(vib_500)
        defect_plc = self.plc_logic.detect(exp_xyz, act_xyz)
        
        is_defect = defect_visual or defect_vib or defect_plc
        
        reasons = []
        if defect_visual: reasons.append("Vision-YOLO")
        if defect_vib: reasons.append("FFT-Vibration")
        if defect_plc: reasons.append("PLC-3D-Dev")
            
        return is_defect, reasons
