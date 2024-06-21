import argparse
import logging
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
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
    parser.add_argument('--end_on_midnight', action='store_true', help="Ends the process so that it can be safely restarted.")
    parser.add_argument("--logfile", type=Path, required=False, help="Write logging to this file instead of to stdout")
    parser.add_argument("--raw_data_dump_dir", type=Path, required=False, help="Dump raw data of unsuccessful reads to this folder.")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    return parser

def _exec_process(params : List[str]) -> None:
    result = subprocess.run(params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rc=result.returncode
    if rc != 0:
        raise Exception("Failed to execute command "+ ' '.join(params)+". Return code was: "+str(result.returncode))

def _run(logger : logging.Logger, read_count : int, end_on_midnight : bool, raw_data_dump_dir : Union[Path, None] = None) -> bool:
    from smart_meter_to_openhab.openhab import OpenhabConnection
    from smart_meter_to_openhab.sml_iskra_mt175 import SmlIskraMt175OneWay

    oh_user=os.getenv('OH_USER') if 'OH_USER' in os.environ else ''
    oh_passwd=os.getenv('OH_PASSWD') if 'OH_PASSWD' in os.environ else ''
    oh_connection = OpenhabConnection(os.getenv('OH_HOST'), oh_user, oh_passwd, logger) # type: ignore
    sml_iskra = SmlIskraMt175OneWay('/dev/ttyUSB0', logger, raw_data_dump_dir)
    logger.info("Connections established. Starting to transfer smart meter values to openhab.")
    start_day=datetime.now().day
    while True:
        logger.info("Reading SML data")
        values=sml_iskra.read_avg(read_count)
        logger.info(f"current values: {values}")
        oh_connection.post_to_items(values)
        logger.info("Values posted to openHAB")
        if values.is_invalid():
            logger.error(f"Reading values from smart meter failed. Exiting process now.")
            return False
        if end_on_midnight and datetime.now().day != start_day:
            logger.info("End of day reached. Exiting process now.")
            return True

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
        success=_run(logger, args.smart_meter_read_count, args.end_on_midnight, raw_data_dump_dir)
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")
    sys.exit(0) if success else sys.exit(1)

if __name__ == '__main__':
    main()