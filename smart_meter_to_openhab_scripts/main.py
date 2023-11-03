import argparse
import logging
import sys
import os
import requests
from pathlib import Path
from time import sleep
from dotenv import load_dotenv
from typing import Union

def create_logger(file : Union[str, None], level ) -> logging.Logger:
    logger = logging.getLogger('smart-meter-to-openhab')
    logger.setLevel(level=level)
    log_handler : Union[logging.FileHandler, logging.StreamHandler] = logging.FileHandler(file) if file else logging.StreamHandler() 
    formatter = logging.Formatter("%(levelname)s: %(asctime)s: %(message)s")
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger

def create_args_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description="Pushing data of ISKRA MT175 smart meter to openhab")
    parser.add_argument("--dotenv_path", type=Path, required=False, help=f"Provide the required environment variables in this .env file \
                        or by any other means (e.g. in your ~/.profile)")
    parser.add_argument("--interval_in_sec", type=int, required=False, default=10, help="Interval in which the data will be read and pushed")
    parser.add_argument("--logfile", type=Path, required=False, help="Write logging to this file instead of to stdout")
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser

def main() -> None:
    parser=create_args_parser()
    args = parser.parse_args()
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
    logger=create_logger(args.logfile, logging.INFO if args.verbose else logging.WARN)
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
        from smart_meter_to_openhab.openhab import OpenhabConnection
        from smart_meter_to_openhab.sml_iskra_mt175 import SmlReader
        oh_user=os.getenv('OH_USER') if 'OH_USER' in os.environ else ''
        oh_passwd=os.getenv('OH_PASSWD') if 'OH_PASSWD' in os.environ else ''
        oh_connection = OpenhabConnection(os.getenv('OH_HOST'), oh_user, oh_passwd, logger) # type: ignore
        sml_reader = SmlReader('/dev/ttyUSB0', logger)
        logger.info("Connections established. Starting to transfer smart meter values to openhab.")
        while True:
            logger.info("Reading SML data")
            values = sml_reader.read_from_sml()
            try:   
                oh_connection.post_to_items(values)
            except requests.exceptions.RequestException as e:
                logger.warning("Caught Exception: " + str(e))
            logger.info(f"current values: L1={values.phase_1_consumption.value} L2={values.phase_2_consumption.value} "\
                        f"L3={values.phase_3_consumption.value} Overall={values.overall_consumption.value} E={values.electricity_meter.value}")
            sleep(args.interval_in_sec)
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")

if __name__ == '__main__':
    main()