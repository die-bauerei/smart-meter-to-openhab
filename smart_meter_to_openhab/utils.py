from datetime import timedelta
from typing import List, Any

def compute_watt_h(value_in_watt : float, measurement_time : timedelta) -> float:
    return value_in_watt*measurement_time.seconds/3600

def add_value_to_rolling_list(list : List[Any], value : Any) -> List[Any]:
    return list[1:]+[value]