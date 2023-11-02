import unittest
import logging
import sys
import os
from typing import Union

from pathlib import Path
package_path=Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(package_path))
from dotenv import load_dotenv
load_dotenv(dotenv_path=f"{package_path}/.env")
from smart_meter_to_openhab.openhab import OpenhabConnection
from smart_meter_to_openhab.interfaces import SmartMeterValues

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestOpenhab(unittest.TestCase):
    oh_host : Union[str, None] = None
    oh_user : Union[str, None] = None
    oh_passwd : Union[str, None] = None
    oh_connection : OpenhabConnection
    smart_meter_values=SmartMeterValues()
    @classmethod
    def setUpClass(cls):
        cls.oh_host=os.getenv('OH_HOST')
        cls.oh_user=os.getenv('OH_USER')
        cls.oh_passwd=os.getenv('OH_PASSWD')
        cls.oh_connection=OpenhabConnection(oh_host=cls.oh_host, oh_user=cls.oh_user, oh_passwd=cls.oh_passwd, logger=logger) # type: ignore

    def setUp(self) -> None:
        # this is called before each test
        TestOpenhab.smart_meter_values.phase_1_consumption.value=0
        TestOpenhab.smart_meter_values.phase_2_consumption.value=0
        TestOpenhab.smart_meter_values.phase_3_consumption.value=0
        TestOpenhab.smart_meter_values.overall_consumption.value=0
        TestOpenhab.smart_meter_values.electricity_meter.value=0
        TestOpenhab.oh_connection.post_to_items(TestOpenhab.smart_meter_values)

    def test_push_to_openhab(self) -> None:
        TestOpenhab.smart_meter_values.phase_1_consumption.value=100
        TestOpenhab.smart_meter_values.phase_2_consumption.value=200
        TestOpenhab.smart_meter_values.phase_3_consumption.value=300
        TestOpenhab.smart_meter_values.overall_consumption.value=600
        TestOpenhab.smart_meter_values.electricity_meter.value=2.5
        TestOpenhab.oh_connection.post_to_items(TestOpenhab.smart_meter_values)
        new_values = TestOpenhab.oh_connection.get_from_items(TestOpenhab.smart_meter_values.convert_to_oh_item_list())
        self.assertEqual(new_values, TestOpenhab.smart_meter_values)

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")