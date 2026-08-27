# Implementation Plan: ISO Digital Twin

## Phase 1: Foundation & Architecture Setup
- [x] Design architecture and conceptual flow (`docs/`)
- [x] Establish logging mechanism (`Runner.md`)
- [x] Import reference materials (`docs/References`)
- [x] Create `requirements.txt`

## Phase 2: Core Simulation Engine (SimPy)
- [x] Define the `FactoryEnv` (Stations A->E, including Dark Zone).
- [x] Define `Operators` (skills, fatigue tracking, transition penalties).
- [x] Implement `main_sim.py` to run the simulation loop in a background thread.

## Phase 3: ISO Pillars (The Core Logic)
- [x] **S-TATECON (`core/statecon.py`)**: SQLite DB connection, Phantom State veto logic, BOM parsing.
- [x] **I-DENDEF (`core/idendef.py`)**: Scikit-learn Anomaly Detection (Isolation Forest) on dummy telemetry, fatigue degradation.
- [x] **O-PTINECK (`core/optineck.py`)**: Bottleneck detection (DEY calculation), GA reallocation with Switching Cost Hysteresis.

## Phase 4: Visualization
- [x] Set up `db.py` to manage SQLite schema for live state.
- [x] Implement `app.py` (Streamlit Dashboard) to visualize DEY, bottlenecks, and S-TATECON vetoes in real-time.

## Phase 5: Integration & Testing
- [ ] Connect SimPy outputs to the SQLite database.
- [ ] Validate end-to-end flow: Phantom state conflict -> Veto -> Defect detected -> DEY drops -> Rebalance vetoed/approved.
- [ ] Finalize code and update documentation.
