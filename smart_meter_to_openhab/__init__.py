import os

if 'OH_HOST' not in os.environ:
    raise ValueError(f"Failed to initialize smart_meter_to_openhab. Required env variable 'OH_HOST' not found")