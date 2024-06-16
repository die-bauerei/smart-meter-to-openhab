import os

if 'OH_HOST' not in os.environ:
    raise ValueError(f"Failed to initialize smart_meter_to_openhab. Required env variable 'OH_HOST' not found")

# TODO: nothing is required
if 'OVERALL_CONSUMPTION_WATT_OH_ITEM' not in os.environ:
    raise ValueError(f"Failed to initialize smart_meter_to_openhab. Required env variable 'OVERALL_CONSUMPTION_WATT_OH_ITEM' not found")