# Implementation Plan: ISO Digital Twin (V2 Remodel)

## Phase 1: Foundation & Architecture Setup
- [x] Design architecture and conceptual flow (`docs/`)
- [x] Establish logging mechanism (`Runner.md`)
- [x] Import reference materials (`docs/References/Flowchart.png` added)
- [ ] Update `requirements.txt` (Add `torch` or `tensorflow`)

- [x] **I-DENDEF Upgrade**: Replaced basic logic with 3 distinct models: PyTorch Vision CNN, Time-Series Vibration Anomaly (Isolation Forest), and PLC Logic Checker. All trained on synthetic data.

## Phase 3: The Central Veto Engine
- [x] Create `core/veto_engine.py`.
- [x] Implement sequential checks: Severity Override (Catastrophic Jam), Material Check (Starvation Risk), Whiplash Veto (Cooldown), Physics Check (Conveyor Speed).

## Phase 4: SimPy Environment Remodel
- [ ] **Buffers**: Add Buffer Queues between stations in `simulation/factory_env.py` to handle "Throttle Flow / Sub-line Buffering" when Severity Override triggers.
- [ ] **Inventory**: Integrate `simpy.Container` to physically model raw material inventory and trigger the Material Check starvation naturally.

## Phase 5: Dashboard & Integration
- [x] Update `core/optineck.py` to use strict time-based boundary checks.
- [x] Refactor `core/statecon.py` as a singleton holding global variables.
- [x] Replace Streamlit with a native Tkinter desktop window (`gui_dashboard.py`).
