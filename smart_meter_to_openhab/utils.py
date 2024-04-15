from datetime import timedelta
from typing import List, Any

def compute_watt_h(value_in_watt : float, measurement_time : timedelta) -> float:
    return value_in_watt*measurement_time.seconds/3600

def manage_rolling_list(list : List[Any], max_value_count : int, new_end_value : Any) -> List[Any]:
    if len(list) < max_value_count:
        return list+[new_end_value]
    else:
        return list[1:]+[new_end_value]