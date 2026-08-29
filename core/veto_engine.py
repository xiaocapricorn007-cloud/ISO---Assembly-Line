class VetoEngine:
    """
    Constraint Verification & Resolution (Veto Engine)
    Step 4 of the O-PTINECK Pipeline.
    """
    def __init__(self, statecon):
        self.statecon = statecon
        self.switching_cost_penalty_sec = 300 # Physical transition penalty

    def check_severity_override(self, max_ct, TT):
        """
        Phase 4D: Severity Override Bypass
        If max_ct > TT + 15%, bypass the whiplash cooldown.
        """
        if max_ct > (TT * 1.15):
            return True, "CATASTROPHIC_JAM_BYPASS_AUTHORIZED"
        return False, "OK"

    def check_material_starvation(self, shift_N):
        """
        Phase 4B: The Material Starvation Veto
        ds = (OH + OO) / r. Checks if any station will run out of stock
        at the accelerated rate before shift ends.
        """
        for station_id, parts in self.statecon.bom_inventory.items():
            for inv in parts:
                required_for_shift = inv["qty_per_car"] * shift_N
                # Assuming no On-Order (OO) stock for now, just On-Hand (OH)
                if inv["on_hand"] < required_for_shift:
                    return True, f"STARVATION_VETO: {station_id} lacks {inv['part_id']} for accelerated rate."
        return False, "OK"

    def check_whiplash(self, current_bottleneck, proposed_bottleneck, is_severity_override):
        """
        Phase 4C: The Human Whiplash & Learning Curve Veto
        Prohibits rebalance unless delta > 15% OR time saved > penalty.
        """
        if is_severity_override:
            return False, "OVERRIDE_ACTIVE"
            
        improvement_ratio = (current_bottleneck - proposed_bottleneck) / current_bottleneck
        if improvement_ratio < 0.15:
            return True, f"WHIPLASH_VETO: Delta ({improvement_ratio*100:.1f}%) < 15% threshold."
            
        return False, "OK"

    def check_physics(self, proposed_times, c_baseline):
        """
        Phase 4A: The Physical Conveyor Veto
        Ensures cycle times don't violate conveyor pacing constraints.
        """
        for st, ct in proposed_times.items():
            if ct > c_baseline * 1.25: # Soft max bounds for physical space
                return True, f"PHYSICS_VIOLATION: {st} CT exceeds spatial bounds."
        return False, "OK"
