import unittest
import logging
import sys
import os
from typing import Union

from smart_meter_to_openhab.openhab import OpenhabConnection
from smart_meter_to_openhab.interfaces import *

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

    def test_valid_values(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        TestOpenhab.oh_connection.post_to_items(values)
        new_values = TestOpenhab.oh_connection.get_values_from_items()
        self.assertEqual(new_values, values)

    def test_none_values(self) -> None:
        values=SmartMeterValues()
        values.phase_1_consumption.value=100
        values.phase_3_consumption.value=300
        values.overall_consumption.value=600
        TestOpenhab.oh_connection.post_to_items(values)
        new_values = TestOpenhab.oh_connection.get_values_from_items()
        self.assertNotEqual(new_values, values)
        values=SmartMeterValues(100, 0, 300, 600, 0)
        self.assertEqual(new_values, values)

    def test_unspecified_oh_items(self) -> None:
        oh_item_names : SmartMeterOhItemNames = (SmartMeterValues.oh_item_names()[0], 
                                                 '', 
                                                 SmartMeterValues.oh_item_names()[2],
                                                 SmartMeterValues.oh_item_names()[3],
                                                 '')
        values=SmartMeterValues(100, 200, 300, 600, 4.5, oh_item_names)
        TestOpenhab.oh_connection.post_to_items(values)
        new_values = TestOpenhab.oh_connection.get_values_from_items()
        self.assertNotEqual(new_values, values) # different item names and values
        values=SmartMeterValues(100, 200, 300, 600, 4.5)
        self.assertNotEqual(new_values, values) # different values
        values=SmartMeterValues(100, 0, 300, 600, 0)
        self.assertEqual(new_values, values)

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")