from typing import List, Any

PersistenceValuesType = List[List[float]]

def manage_rolling_list(list : List[Any], max_value_count : int, new_end_value : Any) -> List[Any]:
    if len(list) < max_value_count:
        return list+[new_end_value]
    else:
        return list[1:]+[new_end_value]