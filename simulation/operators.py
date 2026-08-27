class Operator:
    def __init__(self, op_id, base_speed_multiplier):
        self.op_id = op_id
        self.base_speed_multiplier = base_speed_multiplier
        self.current_station = None
        
    def get_speed_for_station(self, station_id):
        # In a real scenario, this would check a competency matrix.
        # For simplicity, we just return the base multiplier.
        return self.base_speed_multiplier
