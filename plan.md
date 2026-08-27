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
- [x] **Repair Mechanics**: Implemented a 50s sim-time shutdown repair loop when anomalies trigger to properly model downtime.

## Phase 5: Web Dashboard & Integration
- [x] Update `core/optineck.py` to use strict time-based boundary checks.
- [x] Refactor `core/statecon.py` as a singleton database layer.
- [x] Scrapped Tkinter for a native **Flask + Chart.js Web Dashboard** (`web_app.py`, `templates/index.html`).
- [x] Implemented multi-line overlaid vibration charts, collapsible topology trees, and live Timelogs.
- [x] Enforced SQLite persistence wiping on `masterstart` boot to prevent ghost anomalies.
