import argparse
import logging
import os
import sys
import subprocess
from datetime import timedelta, datetime
from pathlib import Path
from time import sleep
from dotenv import load_dotenv
from typing import Union, List

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

def log_level_from_arg(verbosity_count : int) -> int:
    if verbosity_count == 0:
        return logging.ERROR
    if verbosity_count == 1:
        return logging.WARN
    if verbosity_count == 2:
        return logging.INFO
    return logging.DEBUG
    
def create_args_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=f"A tool to push data of ISKRA MT175 smart meter to openHAB. Version {__version__}")
    parser.add_argument("--dotenv_path", type=Path, required=False, help=f"Provide the required environment variables in this .env file \
                        or by any other means (e.g. in your ~/.profile)")
    parser.add_argument("-c", "--smart_meter_read_count", type=int, required=False, default=5, 
                        help="Specifies the number of performed reads that are averaged per interval. Between each read is a sleep of 1 sec.")
    parser.add_argument("--max_reinit", type=int, required=False, default=5, help="Exit process with Return Code 1 when pinging stays unsuccessful.")
    parser.add_argument('--uhubctl', action='store_true', help="Use uhubctl to power off and on the usb port on reinit")
    parser.add_argument("--logfile", type=Path, required=False, help="Write logging to this file instead of to stdout")
    parser.add_argument("--raw_data_dump_dir", type=Path, required=False, help="Dump raw data of unsuccessful reads to this folder.")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    return parser

def _exec_process(params : List[str]) -> None:
    result = subprocess.run(params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rc=result.returncode
    if rc != 0:
        raise Exception("Failed to execute command "+ ' '.join(params)+". Return code was: "+str(result.returncode))

def _run(logger : logging.Logger, read_count : int, use_uhubctl : bool, raw_data_dump_dir : Union[Path, None] = None) -> bool:
    from smart_meter_to_openhab.openhab import OpenhabConnection
    from smart_meter_to_openhab.sml_iskra_mt175 import SmlIskraMt175OneWay
    from smart_meter_to_openhab.sml_reader import SmlReader
    from smart_meter_to_openhab.interfaces import SmartMeterValues
    from smart_meter_to_openhab.utils import add_value_to_rolling_list

    oh_user=os.getenv('OH_USER') if 'OH_USER' in os.environ else ''
    oh_passwd=os.getenv('OH_PASSWD') if 'OH_PASSWD' in os.environ else ''
    oh_connection = OpenhabConnection(os.getenv('OH_HOST'), oh_user, oh_passwd, logger) # type: ignore
    sml_iskra = SmlIskraMt175OneWay('/dev/ttyUSB0', logger, raw_data_dump_dir)
    sml_reader = SmlReader(logger)
    logger.info("Connections established. Starting to transfer smart meter values to openhab.")
    desired_number_of_persistence_values=4
    datetimes_before_post_to_oh=[datetime.now()]*desired_number_of_persistence_values
    ping_timedelta = timedelta(seconds=read_count*sml_iskra.estimated_max_read_time_in_sec*desired_number_of_persistence_values)
    logger.info(f"Calculated ping_timedelta is {ping_timedelta}. Process will be reinit if no data change is detected in the openHAB DB in the given timeframe.")
    run_start_time=datetime.now()
    ping_succeeded=False
    while True:
        logger.info("Reading SML data")
        ref_smart_meter_value=oh_connection.get_median_from_items(SmartMeterValues.oh_item_names())
        values, extended_values=sml_reader.read_avg_from_sml_and_compute_extended_values(sml_iskra, read_count, 
                                                                                         ref_values=ref_smart_meter_value)
        logger.info(f"current values: {values}")
        logger.info(f"current extended values: {extended_values}")
        datetimes_before_post_to_oh=add_value_to_rolling_list(datetimes_before_post_to_oh, datetime.now())
        oh_connection.post_to_items(values)
        oh_connection.post_to_items(extended_values)
        logger.info("Values posted to openHAB")
        # start pinging after running for the specified time
        if (datetime.now() - run_start_time) > ping_timedelta:
            # NOTE: exclude the latest values since oh sometimes has not handled the post requests from above yet.
            if not oh_connection.check_if_persistence_values_updated(SmartMeterValues.oh_item_names(), 
                                                                     start_time=datetimes_before_post_to_oh[0], 
                                                                     end_time=datetimes_before_post_to_oh[-1]):
                break
            ping_succeeded=True
            logger.info("openHAB items ping successful.")
    
    if use_uhubctl:
        logger.error("openHAB items seem to have not been updated - Power off and on usb ports and reinit process")
        # TODO: sudo reboot seems to help a lot more. But lets try this first
        _exec_process(["sudo", "uhubctl", "-a", "cycle", "-d", "10", "-p", "1-5"])
        sleep(1)
    else:
        logger.error("openHAB items seem to have not been updated - reinit process")
    
    return ping_succeeded

def main() -> None:
    parser=create_args_parser()
    args = parser.parse_args()
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
    logger=create_logger(args.logfile)
    logger.setLevel(logging.INFO)
    logger.info(f"Starting smart_meter_to_openhab version {__version__}")
    logger.setLevel(log_level_from_arg(args.verbose))
    try:
        raw_data_dump_dir=args.raw_data_dump_dir if args.raw_data_dump_dir else None
        # TODO: remove the reinit thingy. Let it fail and restart by systemd or so
        unsuccessful_reinit_count=0
        while unsuccessful_reinit_count < args.max_reinit:
            if _run(logger, args.smart_meter_read_count, args.uhubctl, raw_data_dump_dir):
                unsuccessful_reinit_count=0
            else:
                unsuccessful_reinit_count+=1
                logger.error("No improvement after reinit. Trying again.")

    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")
    
    logger.error("Unable to upload valid data to openHAB. Exiting Process with Return Code 1.")
    sys.exit(1)

if __name__ == '__main__':
    main()