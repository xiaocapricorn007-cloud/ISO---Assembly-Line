# ISO Digital Twin: Technical Evaluation

## 1. System Overview & Stack
The ISO Digital Twin is an advanced, predictive, closed-loop simulation environment designed for mixed-model automotive assembly lines. It transcends traditional reactive dashboards by acting as a constraint-aware prediction engine that anticipates failures, models physical boundaries, and optimizes flow *before* physical breakdowns occur.

**Core Stack:**
- **Simulation Engine:** Python with **SimPy**. The physics engine operates on a rigid, synchronous "pulsed" master loop (`master_line_loop`), explicitly mirroring real-world takt times.
- **Backend Server:** **Flask** serves as the API and Web Server.
- **Frontend Dashboard:** Modern **HTML5, Tailwind CSS, and Chart.js**. It features 60FPS multi-line overlaid telemetry charts and a custom CSS-driven physical flow simulation that maps perfectly to backend spatial coordinates.
- **Database:** **SQLite**. The singleton database layer (S-TATECON) handles real-time telemetry logging, global variables, inventory state, and machine statuses.
- **Machine Learning:** **PyTorch** and **Scikit-Learn** power the predictive diagnostics and evaluation matrix.

---

## 2. The Granular Pipeline & Architecture
The factory floor was expanded from 5 monolithic stations (Pressing, Welding, Painting, PowerTrain, Final Assembly) into **16 distinct granular machines**, operating alongside a designated human workforce.

The pipeline is split into three interdependent pillars governed by a single unifying metric—the **Dynamic Equilibrium Yield (DEY)**.

### Pillar 1: S-TATECON (Central State Management)
Serving as the digital ontology and single source of truth, S-TATECON is a Singleton database layer. It natively tracks:
- **Global Constraints:** Target cycle times (10s processing, 5s transit), shift capacities, and structural efficiency ($\eta$).
- **Live Inventory (BOM):** Physically models raw materials using `simpy.Container`. If a station starves, it halts the entire synchronized line until a forklift replenishes the required parts.
- **Machine State Tracking:** Transitions machines smoothly between `RUNNING`, `BROKEN`, `STARVED`, and `IDLE`.

### Pillar 2: I-DENDEF (Predictive Quality & Defect Detection)
Instead of hardcoded rules, I-DENDEF runs deep-learning ML models concurrently across all 16 machines to act as a predictive quality guard.
- **Vibration TCN-AutoEncoders:** Evaluates high-frequency spectral reconstruction via FFT (Fast Fourier Transform) to detect mechanical *Bearing Degradation*.
- **PLC Kinematics TCN-AutoEncoders:** Evaluates 3D spatial trajectories (X, Y, Z coordinates) utilizing `AdaptiveAvgPool1d` against a strict 2.0mm tolerance to detect progressive *Tool Miscalibration* and sudden *Catastrophic Collisions*.
- **Training & Inference:** The models are uniquely pre-trained on 3,000 synthetic baseline samples per machine over 60 epochs. Inference runs dynamically from saved `.pth` weights, utilizing a rigorous Z-Score statistical threshold (`mean + 4*std`) to completely eliminate false positives.

### Pillar 3: O-PTINECK (Proactive Flow Optimizer) & The Veto Engine
O-PTINECK dynamically tracks the line's efficiency using the DEY calculation: `DEY = (3600 / max(CT)) * eta`. 
When a bottleneck forms, O-PTINECK deploys a Heuristic Genetic Algorithm to mathematically reallocate workloads and drop the maximum cycle time.

However, standard optimizers cause factory chaos by rebalancing at every micro-delay. O-PTINECK routes all optimizations through a centralized **Veto Engine** which enforces:
1. **Severity Override:** Overrides optimizations if catastrophic jamming is detected.
2. **Material Check:** Vetoes the rebalance if S-TATECON lacks the BOM stock to handle the increased speed.
3. **Physics Check:** Rejects speeds that physically exceed the conveyor bounds.
4. **Whiplash Hysteresis:** Mathematically vetoes the optimization if the projected time saved does not exceed the physical penalty of transitioning humans and tooling.

---

## 3. Simulation Physics & Inbuilt Features
- **Rigid Pulsed Synchronization:** All 16 machines process simultaneously for exactly 10s. Then, all telemetry flatlines, all machines drop to `IDLE`, and the conveyor translates the parts for exactly 5s. 
- **Global Pausing:** A master toggle seamlessly freezes the SimPy physics engine, SQLite database updates, and frontend CSS animations in real-time. Telemetry streams instantly drop to a flatline while paused.
- **Full-Screen Station Topology Modal:** An interactive carousel allowing operators to click the flowchart and dive into specific stations, visually mapping the live deployment of Orange machine dots and White human operator dots.
- **Automated Data Wiping:** Booting the master orchestrator automatically truncates all ghost records from previous runs, ensuring a completely stable start.

---

## 4. Evaluation Metrics & Ground Truth Matrix
Because the simulation generates both the synthetic anomalies (Ground Truth) and the ML Predictions (Inference) independently, it acts as a perfect closed-loop testing ground.

Upon intercepting a graceful shutdown (`Ctrl+C` in `masterstart.py`), the Digital Twin automatically dumps a comprehensive **Scikit-Learn Evaluation Matrix** to the terminal, detailing:
- **ROC-AUC (Receiver Operating Characteristic)**
- **PR-AUC (Precision-Recall Area Under Curve)**
- **F1-Scores**
- **Confusion Matrix:** True Positives (Caught), False Positives (False Alarms), True Negatives, and False Negatives (Missed Defects).
- **Average MSE** distributions between Normal and Anomalous runs.
