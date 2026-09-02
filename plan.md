# Implementation Plan: ISO Digital Twin (V2 Remodel)

## Phase 1: Foundation & Architecture Setup
- [x] Design architecture and conceptual flow (`docs/`)
- [x] Establish logging mechanism (`Runner.md`)
- [x] Import reference materials (`docs/References/Flowchart.png` added)
- [x] Update `requirements.txt` (Added `torch`, `flask`, etc.)

## Phase 2: Granular I-DENDEF & ML Pipeline
- [x] **Machine Granularity**: Expanded the 5 monolithic stations into 16 distinct sub-machines using `simpy.Resource`.
- [x] **TCN AutoEncoder**: Implemented 1D-Convolution AutoEncoders in PyTorch for vibration sequence reconstruction.
- [x] **Pre-Training**: Wrote `train_vibration.py` to generate distinct synthetic baselines for all 16 machines, pre-train them, and save thresholds.
- [x] **Inference Pipeline**: `idendef.py` dynamically loads the 16 `.pth` weights to evaluate anomalies without retraining.

## Phase 3: The Central Veto Engine
- [x] Create `core/veto_engine.py`.
- [x] Implement sequential checks: Severity Override (Catastrophic Jam), Material Check (Starvation Risk), Whiplash Veto (Cooldown), Physics Check (Conveyor Speed).

## Phase 4: SimPy Environment Remodel
- [x] **Buffers**: Add Buffer Queues between stations in `simulation/factory_env.py` to handle "Throttle Flow / Sub-line Buffering".
- [x] **Inventory**: Integrate `simpy.Container` to physically model raw material inventory.
- [x] **(Scrapped) Repair Mechanics**: The 50s sim-time shutdown repair loop was scrapped to favor a continuous, rigid pulsed simulation flow where anomalous machines merely delay their single cycle.

## Phase 5: Web Dashboard & Integration
- [x] Update `core/optineck.py` to use strict time-based boundary checks.
- [x] Refactor `core/statecon.py` as a singleton database layer.
- [x] Scrapped Tkinter for a native **Flask + Chart.js Web Dashboard** (`web_app.py`, `templates/index.html`).
- [x] Implemented multi-line overlaid vibration charts, collapsible topology trees, and live Timelogs.
- [x] Enforced SQLite persistence wiping on `masterstart` boot to prevent ghost anomalies.

## Phase 6: Multi-Modal Diagnostics & S-TATECON Flow
- [x] **3D PLC Trajectories**: Implemented spatial kinematics (`X`, `Y`, `Z`) autoencoders using AdaptiveAvgPool1d to detect Tool Miscalibration anomalies.
- [x] **Model Tuning**: Deepened TCN Autoencoder epochs, tripled datasets, and implemented rigorous Z-Score statistical thresholding to eliminate false positives and boost PR-AUC.
- [x] **Evaluation Matrix**: Intercept `Ctrl+C` in `masterstart.py` to dump a full Scikit-Learn evaluation matrix (ROC-AUC, PR-AUC, F1-Scores) comparing hidden Ground Truths to ML Predictions.
- [x] **Visual Assembly Flowchart**: Overhauled the S-TATECON dashboard tab with a highly-polished decoupled CSS-driven animation simulating multi-part physical transit along the conveyor line.
- [x] **(Scrapped) Flowchart Inventory Logic**: Decided NOT to bind the SimPy block inventory directly to the visual flowchart DOM elements to prevent UI clutter. The inventory remains tracked via the dedicated S-TATECON inventory table tab instead.

## Phase 7: Real-time Synchronized Pulsed Line
- [x] **Strict Cycle Sync**: Overhauled the asynchronous simulation engine into a globally synchronized \master_line_loop\. All 16 machines process simultaneously (10s) and transit simultaneously (5s).
- [x] **Global Pausing**: Implemented a \simulation_running\ SQLite flag and a custom \pausable_timeout\ generator in SimPy, allowing the UI's Start/Pause button to seamlessly freeze the physics engine, database updates, and CSS animations in real time.
- [x] **Visual State Fidelity**: Removed UI desync bugs. Machines are explicitly forced to \IDLE\ in the database exactly when the dots visually begin traversing the conveyor belt. 
- [x] **Cycle Time Alignment**: Fixed hidden hardcoded station overrides in \statecon.py\ that were disrupting the 10.0s global \	arget_cycle_time\. The pipeline now flawlessly pulses exactly as intended.
