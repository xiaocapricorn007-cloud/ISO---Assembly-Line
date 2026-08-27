# S-TATECON (Central Control Engine)

S-TATECON acts as the digital ontology and single source of truth for the ISO Digital Twin. It manages the live state of the factory and strictly prevents the twin from optimizing against ghost data.

## Core Directives

1. **The Phantom State Trap (Auto-Validation Layer)**
   - **Problem:** Standard digital twins rely heavily on human dashboard inputs, which causes catastrophic lag during crises. If an operator updates the shift target ($N$) or time ($T$), but the master conveyor PLC reports a stoppage, relying on the human input creates a "Phantom State."
   - **Solution:** S-TATECON features an Auto-Validation layer that checks human inputs against live PLC (Programmable Logic Controller) binary data. If a conflict occurs, S-TATECON freezes AI optimization and enforces the PLC reality.

2. **Predictive Inventory Depletion**
   - Calculates dynamic Days-Supply ($ds$) to prevent starvation.
   - **Formula:** $ds = \frac{OH + OO}{r}$ (On-Hand + On-Order divided by dynamic daily requirement).
   - **Active Quality Quarantine Veto:** On-Order stock that fails QA is explicitly NOT calculated into available buffers.

3. **Live BOM Tracking**
   - Tracks specific features ($f$) and options ($k$) required for each unique vehicle (Job $j$), informing downstream modules (like O-PTINECK) of expected workloads and cycle times at specific stations.
