import unittest
import logging
import sys
import os
from typing import Union

from pathlib import Path
package_path=Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(package_path))
from dotenv import load_dotenv
if os.path.isfile(f"{package_path}/.env"):
    load_dotenv(dotenv_path=f"{package_path}/.env")
from smart_meter_to_openhab.openhab import OpenhabConnection
from smart_meter_to_openhab.interfaces import SmartMeterValues, ExtendedSmartMeterValues

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

class TestOpenhab(unittest.TestCase):
    oh_host : Union[str, None] = None
    oh_user : Union[str, None] = None
    oh_passwd : Union[str, None] = None
    oh_connection : OpenhabConnection
    @classmethod
    def setUpClass(cls):
        cls.oh_host=os.getenv('OH_HOST')
        cls.oh_user=os.getenv('OH_USER')
        cls.oh_passwd=os.getenv('OH_PASSWD')
        cls.oh_connection=OpenhabConnection(oh_host=cls.oh_host, oh_user=cls.oh_user, oh_passwd=cls.oh_passwd, logger=logger) # type: ignore

    def setUp(self) -> None:
        # this is called before each test
        values=SmartMeterValues(0, 0, 0, 0, 0)
        TestOpenhab.oh_connection.post_to_items(values)
        extended_values=ExtendedSmartMeterValues(0)
        TestOpenhab.oh_connection.post_to_items(extended_values)

    def test_valid_values(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        TestOpenhab.oh_connection.post_to_items(values)
        new_values = TestOpenhab.oh_connection.get_values_from_items(SmartMeterValues.oh_item_names)
        self.assertEqual(new_values, values)

        extended_values=ExtendedSmartMeterValues(0.6)
        TestOpenhab.oh_connection.post_to_items(extended_values)
        new_extended_values = TestOpenhab.oh_connection.get_extended_values_from_items(ExtendedSmartMeterValues.oh_item_names)
        self.assertEqual(new_extended_values, extended_values)

    def test_none_values(self) -> None:
        values=SmartMeterValues()
        values.phase_1_consumption.value=100
        values.phase_3_consumption.value=300
        values.overall_consumption.value=600
        TestOpenhab.oh_connection.post_to_items(values)
        new_values = TestOpenhab.oh_connection.get_values_from_items(SmartMeterValues.oh_item_names)
        self.assertNotEqual(new_values, values)
        values=SmartMeterValues(100, 0, 300, 600, 0)
        self.assertEqual(new_values, values)

        extended_values=ExtendedSmartMeterValues()
        TestOpenhab.oh_connection.post_to_items(extended_values)
        new_extended_values = TestOpenhab.oh_connection.get_extended_values_from_items(ExtendedSmartMeterValues.oh_item_names)
        self.assertNotEqual(new_extended_values, extended_values)
        extended_values=ExtendedSmartMeterValues(0)
        self.assertEqual(new_extended_values, extended_values)

    def test_unspecified_oh_items(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 4.5)
        values.phase_1_consumption.value=100
        values.phase_2_consumption.oh_item=''
        values.phase_3_consumption.value=300
        values.overall_consumption.value=600
        values.electricity_meter.oh_item=''
        TestOpenhab.oh_connection.post_to_items(values)
        new_values = TestOpenhab.oh_connection.get_values_from_items(SmartMeterValues.oh_item_names)
        self.assertNotEqual(new_values, values) # different item names and values
        values=SmartMeterValues(100, 200, 300, 600, 4.5)
        self.assertNotEqual(new_values, values) # different values
        values=SmartMeterValues(100, 0, 300, 600, 0)
        self.assertEqual(new_values, values)

        extended_values=ExtendedSmartMeterValues(0.6)
        extended_values.overall_consumption_wh.oh_item=''
        TestOpenhab.oh_connection.post_to_items(extended_values)
        new_extended_values = TestOpenhab.oh_connection.get_extended_values_from_items(ExtendedSmartMeterValues.oh_item_names)
        self.assertNotEqual(new_extended_values, extended_values) # different item names and values
        extended_values=ExtendedSmartMeterValues(0.6)
        self.assertNotEqual(new_extended_values, extended_values) # different values
        extended_values=ExtendedSmartMeterValues(0)
        self.assertEqual(new_extended_values, extended_values)

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")