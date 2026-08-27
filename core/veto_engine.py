class VetoEngine:
    """
    Constraint Verification & Resolution (Veto Engine)
    Centralizes all veto checks before execution.
    """
    def __init__(self):
        self.switching_cost_penalty_sec = 300 # 5 minutes

    def check_severity_override(self, max_ct, target_ct):
        """
        Catastrophic Jam Check.
        If cycle time exceeds target by 2x, it's a catastrophic jam.
        Action: Throttle Flow / Sub-line Buffering.
        """
        if max_ct > (target_ct * 2.0):
            return True, "CATASTROPHIC_JAM_DIVERT_TO_BUFFER"
        return False, "OK"

    def check_material_starvation(self, current_inventory, depletion_rate):
        """
        Material Check (Starvation Risk).
        ds = (OH + OO) / r
        """
        if depletion_rate > 0:
            days_supply = current_inventory / depletion_rate
            if days_supply < 1.0: # Less than 1 "shift" of inventory left
                return True, "STARVATION_RISK_THROTTLE_SPEED"
        return False, "OK"

    def check_whiplash(self, projected_time_saved_sec):
        """
        Whiplash Veto (Cooldown Check).
        Prevents GA from rebalancing if transition penalty > saved time.
        """
        if projected_time_saved_sec < self.switching_cost_penalty_sec:
            return True, "WHIPLASH_VETO_MOVE_DENIED"
        return False, "OK"

    def check_physics(self, expected_velocity, actual_velocity, tolerance=0.1):
        """
        Physics Check (Conveyor Speed v=w/c).
        Ensures the Twin isn't optimizing against impossible physics.
        """
        if abs(expected_velocity - actual_velocity) > tolerance:
            return True, "PHYSICS_VIOLATION_VETO"
        return False, "OK"

    def evaluate_all(self, max_ct, target_ct, inv, dep_rate, time_saved, exp_v, act_v):
        """
        Runs the sequential veto pipeline from the flowchart.
        """
        sev_flag, sev_msg = self.check_severity_override(max_ct, target_ct)
        if sev_flag: return sev_msg

        mat_flag, mat_msg = self.check_material_starvation(inv, dep_rate)
        if mat_flag: return mat_msg

        whip_flag, whip_msg = self.check_whiplash(time_saved)
        if whip_flag: return whip_msg

        phys_flag, phys_msg = self.check_physics(exp_v, act_v)
        if phys_flag: return phys_msg

        return "ALL_CHECKS_PASSED"
