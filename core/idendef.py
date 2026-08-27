import numpy as np
from sklearn.ensemble import IsolationForest

class IdendefEngine:
    """
    I-DENDEF: Predictive Quality Guard
    Handles Mechanical Anomaly Detection and Fatigue Tracking.
    """
    def __init__(self):
        # Pre-train a lightweight Isolation Forest on dummy "normal" vibration/heat data
        self.model = IsolationForest(contamination=0.05, random_state=42)
        # Generate dummy normal data (heat, vibration)
        X_train = np.random.normal(loc=[50.0, 2.0], scale=[5.0, 0.5], size=(100, 2))
        self.model.fit(X_train)
        
    def detect_mechanical_anomaly(self, heat, vibration):
        """
        Simulates AI inference on edge telemetry.
        Returns True if anomaly (defect) is detected.
        """
        X_test = np.array([[heat, vibration]])
        pred = self.model.predict(X_test)
        # IsolationForest returns -1 for anomalies, 1 for normal
        return pred[0] == -1

    def calculate_fatigue_multiplier(self, shift_time_hours, base_multiplier=1.0):
        """
        Wright's Learning Curve / Fatigue Simulation.
        As shift progresses, fatigue increases cycle time.
        """
        # Simplistic fatigue model: after 4 hours, cycle time increases by 10% per hour
        if shift_time_hours > 4:
            fatigue = 1.0 + ((shift_time_hours - 4) * 0.1)
        else:
            fatigue = 1.0
        return base_multiplier * fatigue
