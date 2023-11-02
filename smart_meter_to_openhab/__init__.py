import os

required_envs=['OH_HOST','PHASE_1_CONSUMPTION_OH_ITEM', 'PHASE_2_CONSUMPTION_OH_ITEM', 'PHASE_3_CONSUMPTION_OH_ITEM', 
               'OVERALL_CONSUMPTION_OH_ITEM', 'ELECTRICITY_METER_OH_ITEM']

for env_var in required_envs:
    if env_var not in os.environ:
        raise ValueError(f"Failed to initialize smart_meter_to_openhab. Required env variable {env_var} not found")

if os.getenv('OH_HOST').startswith('https'): # type: ignore
    raise ValueError(f"Failed to initialize smart_meter_to_openhab. Only http connection is supported (no ssl)")