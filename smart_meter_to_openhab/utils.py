from datetime import timedelta

def compute_watt_h(value_in_watt : float, measurement_time : timedelta) -> float:
    return value_in_watt*measurement_time.seconds/3600