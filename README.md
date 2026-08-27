# ISO Digital Twin: Assembly Line

A predictive, closed-loop Digital Twin designed specifically for mixed-model automotive assembly lines. Moving beyond reactive dashboards, the ISO ecosystem acts as a paranoid, constraint-aware prediction engine. It anticipates failures, models physical constraints, and optimizes flow before physical execution breaks down on the factory floor.

## Architecture

The architecture is divided into three interdependent pillars, governed by a unifying output metric: the **Dynamic Equilibrium Yield (DEY)**.

1. **[S-TATECON (Central State Management)](docs/S-TATECON.md)**: The digital ontology and single source of truth. Prevents "Phantom State" errors via Auto-Validation against live PLC data.
2. **[I-DENDEF (Predictive Quality & Defect Detection)](docs/I-DENDEF.md)**: The predictive quality guard. Uses edge-deployed AI (Isolation Forests) to monitor high-frequency telemetry at Prime Elements, while tracking human fatigue using Wright's learning curve.
3. **[O-PTINECK (Proactive Flow & Bottleneck Optimizer)](docs/O-PTINECK.md)**: The bottleneck optimizer. Uses "Dark Zone" Inference to calculate missing task times and Genetic Algorithms to reallocate operators, strictly governed by a "Switching Cost Hysteresis" cooldown.

## Getting Started

This repository contains a Python-based simulation (utilizing `SimPy` and `Streamlit`) to model the chaotic factory environment and demonstrate the ISO constraint-satisfaction architecture.

*(Setup and installation instructions will be added as the simulation is built.)*