import argparse
import logging
import sys
import os
import subprocess
from datetime import timedelta, datetime
from pathlib import Path
from time import sleep
from dotenv import load_dotenv
from typing import Union, List
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

try:
    import importlib.metadata
    __version__ = importlib.metadata.version('smart_meter_to_openhab')
except:
    __version__ = 'development'

def create_logger(file : Union[str, None]) -> logging.Logger:
    logger = logging.getLogger('smart-meter-to-openhab')
    log_handler : Union[logging.FileHandler, logging.StreamHandler] = logging.FileHandler(file) if file else logging.StreamHandler() 
    formatter = logging.Formatter("%(levelname)s: %(asctime)s: %(message)s")
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger

def create_args_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=f"A tool to push data of ISKRA MT175 smart meter to openHAB. Version {__version__}")
    parser.add_argument("--dotenv_path", type=Path, required=False, help=f"Provide the required environment variables in this .env file \
                        or by any other means (e.g. in your ~/.profile)")
    parser.add_argument("-c", "--smart_meter_read_count", type=int, required=False, default=5, 
                        help="Specifies the number of performed reads that are averaged per interval. Between each read is a sleep of 1 sec.")
    parser.add_argument("--interval_in_sec", type=int, required=False, default=10, help="Interval in which the data will be read and pushed")
    parser.add_argument("--ping_in_min", type=int, required=False, default=10, help="Reinit if no data can be found in the openHAB DB in the given timeframe")
    parser.add_argument("--logfile", type=Path, required=False, help="Write logging to this file instead of to stdout")
    parser.add_argument('--uhubctl', action='store_true', help="Use uhubctl to power off and on the usb port on reinit")
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser

def _exec_process(params : List[str]) -> None:
    result = subprocess.run(params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rc=result.returncode
    if rc != 0:
        raise Exception("Failed to execute command "+ ' '.join(params)+". Return code was: "+str(result.returncode))

def _run(process_start_time : datetime, logger : logging.Logger, read_count : int, interval_in_sec : int, ping_in_min : int, use_uhubctl : bool) -> None:
    from smart_meter_to_openhab.openhab import OpenhabConnection
    from smart_meter_to_openhab.sml_iskra_mt175 import SmlIskraMt175
    from smart_meter_to_openhab.sml_reader import SmlReader
    from smart_meter_to_openhab.interfaces import SmartMeterValues, ExtendedSmartMeterValues

    oh_user=os.getenv('OH_USER') if 'OH_USER' in os.environ else ''
    oh_passwd=os.getenv('OH_PASSWD') if 'OH_PASSWD' in os.environ else ''
    oh_connection = OpenhabConnection(os.getenv('OH_HOST'), oh_user, oh_passwd, logger) # type: ignore
    sml_iskra = SmlIskraMt175('/dev/ttyUSB0', logger)
    sml_reader = SmlReader(logger)
    logger.info("Connections established. Starting to transfer smart meter values to openhab.")
    ping_succeeded = True
    ping_timedelta = timedelta(minutes=ping_in_min)
    while ping_succeeded:
        logger.info("Reading SML data")
        ref_smart_meter_value=oh_connection.get_median_from_items(SmartMeterValues.oh_item_names())
        values, extended_values=sml_reader.read_avg_from_sml_and_compute_extended_values(sml_iskra.read, read_count, ref_smart_meter_value)
        logger.info(f"current values: {values}")
        logger.info(f"current extended values: {extended_values}")
        oh_connection.post_to_items(values)
        oh_connection.post_to_items(extended_values)
        logger.info("Values posted to openHAB")
        # start pinging after process is running for the specified time
        if (datetime.now() - process_start_time) > ping_timedelta:
            logger.info("Ping openHAB items to check if updated")
            ping_succeeded = oh_connection.check_if_updated(SmartMeterValues.oh_item_names(), ping_timedelta) and oh_connection.check_if_updated(
                ExtendedSmartMeterValues.oh_item_names(), ping_timedelta)
        sleep(interval_in_sec)
    
    if use_uhubctl:
        logger.warning("openHAB items seem to have not been updated - Power off and on usb ports and reinit process")
        _exec_process(["sudo", "uhubctl", "-a", "cycle", "-d", "10", "-p", "1-5"])
        sleep(1)
    else:
        logger.warning("openHAB items seem to have not been updated - reinit process")

def main() -> None:
    parser=create_args_parser()
    args = parser.parse_args()
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
    logger=create_logger(args.logfile)
    logger.setLevel(logging.INFO)
    logger.info(f"Starting smart_meter_to_openhab version {__version__}")
    logger.setLevel(logging.INFO if args.verbose else logging.WARN)
    try:
        while True:
            _run(datetime.now(), logger, args.smart_meter_read_count, args.interval_in_sec, args.ping_in_min, args.uhubctl)
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")

if __name__ == '__main__':
    main()