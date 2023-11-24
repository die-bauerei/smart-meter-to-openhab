import unittest
import logging
import sys
import os

from pathlib import Path
package_path=Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(package_path))
from dotenv import load_dotenv
from smart_meter_to_openhab.interfaces import *

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

class TestInterfaces(unittest.TestCase):

    # this is called before each test
    def setUp(self) -> None:
        if os.path.isfile(f"{package_path}/.env"):
            load_dotenv(dotenv_path=f"{package_path}/.env")

    def test_classvar(self) -> None:
        self.assertTrue('unit_tests_smart_meter_phase_1_consumption' in SmartMeterValues._oh_items)
        self.assertTrue('unit_tests_smart_meter_phase_2_consumption' in SmartMeterValues._oh_items)
        self.assertTrue('unit_tests_smart_meter_phase_3_consumption' in SmartMeterValues._oh_items)
        self.assertTrue('unit_tests_smart_meter_overall_consumption' in SmartMeterValues._oh_items)
        self.assertTrue('unit_tests_smart_meter_electricity_meter' in SmartMeterValues._oh_items)
        self.assertEqual('unit_tests_smart_meter_overall_consumption_wh', ExtendedSmartMeterValues._oh_item)

    def test_init(self) -> None:
        values=SmartMeterValues()
        extended_values=ExtendedSmartMeterValues()
        self.assertEqual(values.phase_1_consumption.oh_item, 'unit_tests_smart_meter_phase_1_consumption')
        self.assertEqual(values.phase_2_consumption.oh_item, 'unit_tests_smart_meter_phase_2_consumption')
        self.assertEqual(values.phase_3_consumption.oh_item, 'unit_tests_smart_meter_phase_3_consumption')
        self.assertEqual(values.overall_consumption.oh_item, 'unit_tests_smart_meter_overall_consumption')
        self.assertEqual(extended_values.overall_consumption_wh.oh_item, 'unit_tests_smart_meter_overall_consumption_wh')
        self.assertEqual(values.electricity_meter.oh_item, 'unit_tests_smart_meter_electricity_meter')
        self.assertTrue(all(value is None for value in values.convert_to_value_list()))
        self.assertTrue(all(value is None for value in extended_values.convert_to_value_list()))
        self.assertEqual(len(values.convert_to_value_list()), 5)
        self.assertEqual(len(extended_values.convert_to_value_list()), 1)

    def test_creation(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        new_values=SmartMeterValues.create(values.convert_to_item_value_list())
        self.assertEqual(values, new_values)
        values.phase_1_consumption.value=None
        new_values=SmartMeterValues.create(values.convert_to_item_value_list())
        self.assertEqual(values, new_values)

    def test_creation_not_all_items(self) -> None:
        os.environ['PHASE_1_CONSUMPTION_WATT_OH_ITEM']=''
        values=SmartMeterValues()
        values.phase_2_consumption.value=200
        values.phase_3_consumption.value=300
        new_values=SmartMeterValues.create(values.convert_to_item_value_list())
        self.assertEqual(values, new_values)

    def test_creation_average(self) -> None:
        values_1=SmartMeterValues(100, 200, 300, 600, 2.5)
        values_2=SmartMeterValues(200, 300, 400, 700, 3.5)
        new_values=SmartMeterValues.create_avg([values_1, values_2])
        self.assertEqual(SmartMeterValues(150, 250, 350, 650, 3.0), new_values)

    def test_is_invalid(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        self.assertFalse(values.is_invalid())
        values.phase_1_consumption.value=None
        self.assertTrue(values.is_invalid())

        # NOTE: Even unspecified values should be tested against None. Since we read all values from the smart meter, 
        #   no matter what will be actually posted to openHAB later on.
        os.environ['PHASE_1_CONSUMPTION_WATT_OH_ITEM']=''
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        self.assertFalse(values.is_invalid())
        values.phase_1_consumption.value=None
        self.assertTrue(values.is_invalid())

        # NOTE: The value for watt/h is considered in the extended values
        extended_values=ExtendedSmartMeterValues(0.5)
        self.assertFalse(extended_values.is_invalid())
        extended_values.overall_consumption_wh.value=None
        self.assertTrue(extended_values.is_invalid())

    def test_comparison(self) -> None:
        values_1=SmartMeterValues(100, 200, 300, 600, 2.5)
        values_2=SmartMeterValues(100, 200, 300, 600, 2.5)
        self.assertEqual(values_1, values_2)
        values_3=SmartMeterValues(200, 300, 400, 600, 2.5)
        self.assertNotEqual(values_1, values_3)
        
if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")