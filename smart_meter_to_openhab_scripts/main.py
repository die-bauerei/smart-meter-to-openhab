import argparse
import logging
import sys
import os
from pathlib import Path
from time import sleep
from typing import Union

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from smart_meter_to_openhab.openhab import OpenhabConnection
from smart_meter_to_openhab.sml_iskra_mt175 import SmlReader

logger = logging.getLogger(__name__)

def create_args_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description="Pushing data of ISKRA MT175 smart meter to openhab")
    parser.add_argument("--interval_in_sec", type=int, required=False, default=60, help="Interval in which the data will be read and pushed")
    parser.add_argument("--logfile", type=Path, required=False, help="Write logging to this file instead of to stdout")
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser

def main(interval_in_sec : int, logfile : Union[Path, None] = None, verbose = None) -> None:
    try:
        loglevel=logging.INFO if verbose else logging.WARN
        if logfile:
            logging.basicConfig(filename=logfile, level=loglevel)
        else:
            logging.basicConfig(stream=sys.stdout, level=loglevel)

        oh_connection = OpenhabConnection(os.getenv('OH_HOST'), os.getenv('OH_USER'), os.getenv('OH_PASSWD'), logger) # type: ignore
        sml_reader = SmlReader('/dev/ttyUSB0', logger)
        logger.info("Connections established. Starting to transfer smart meter values to openhab.")
        while True:
            logger.info("Reading SML data")
            values = sml_reader.read_from_sml()
            oh_connection.post_to_items(values)
            logger.info(f"current values: L1={values.phase_1_consumption.value} L2={values.phase_2_consumption.value}" \
                        f"L3={values.phase_3_consumption.value} Overall={values.overall_consumption.value} E={values.electricity_meter.value}")
            sleep(interval_in_sec)
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")

if __name__ == '__main__':
    parser=create_args_parser()
    args = parser.parse_args()
    main(args.interval_in_sec, args.logfile, args.verbose)