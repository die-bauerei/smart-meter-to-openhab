import os

if 'OH_HOST' not in os.environ:
    raise ValueError(f"Failed to initialize smart_meter_to_openhab. Required env variable 'OH_HOST' not found")

if os.getenv('OH_HOST').startswith('https') and 'OH_USER' in os.environ: # type: ignore
    raise ValueError(f"Failed to initialize smart_meter_to_openhab. Only http connection is supported (no ssl)")