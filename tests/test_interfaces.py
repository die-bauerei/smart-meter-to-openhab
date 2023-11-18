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
        self.assertTrue('smart_meter_phase_1_consumption' in SmartMeterValues.oh_item_names)
        self.assertTrue('smart_meter_phase_2_consumption' in SmartMeterValues.oh_item_names)
        self.assertTrue('smart_meter_phase_3_consumption' in SmartMeterValues.oh_item_names)
        self.assertTrue('smart_meter_overall_consumption' in SmartMeterValues.oh_item_names)
        self.assertTrue('smart_meter_overall_consumption_wh' in SmartMeterValues.oh_item_names)
        self.assertTrue('smart_meter_electricity_meter' in SmartMeterValues.oh_item_names)

    def test_init(self) -> None:
        values=SmartMeterValues()
        self.assertEqual(values.phase_1_consumption.oh_item, 'smart_meter_phase_1_consumption')
        self.assertEqual(values.phase_2_consumption.oh_item, 'smart_meter_phase_2_consumption')
        self.assertEqual(values.phase_3_consumption.oh_item, 'smart_meter_phase_3_consumption')
        self.assertEqual(values.overall_consumption.oh_item, 'smart_meter_overall_consumption')
        self.assertEqual(values.overall_consumption_wh.oh_item, 'smart_meter_overall_consumption_wh')
        self.assertEqual(values.electricity_meter.oh_item, 'smart_meter_electricity_meter')
        self.assertTrue(all(value is None for value in values.convert_to_measurement_value_list()))

    def test_creation(self) -> None:
        values=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        new_values=create_smart_meter_values(values.convert_to_item_value_list())
        self.assertEqual(values, new_values)
        values.phase_1_consumption.value=None
        new_values=create_smart_meter_values(values.convert_to_item_value_list())
        self.assertEqual(values, new_values)

    def test_creation_not_all_items(self) -> None:
        os.environ['PHASE_1_CONSUMPTION_WATT_OH_ITEM']=''
        values=SmartMeterValues()
        values.phase_2_consumption.value=200
        values.phase_3_consumption.value=300
        new_values=create_smart_meter_values(values.convert_to_item_value_list())
        self.assertEqual(values, new_values)

    def test_creation_average(self) -> None:
        values_1=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        values_2=SmartMeterValues.create(200, 300, 400, 700, 1.0, 3.5)
        new_values=create_avg_smart_meter_values([values_1, values_2])
        self.assertEqual(SmartMeterValues.create(150, 250, 350, 650, 0.8, 3.0), new_values)

    def test_has_none(self) -> None:
        values=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        self.assertFalse(values.is_valid_measurement())
        values.phase_1_consumption.value=None
        self.assertTrue(values.is_valid_measurement())

        # NOTE: Even unspecified values should be tested against None. Since we read all values from the smart meter, 
        #   no matter what will be actually posted to openHAB later on.
        os.environ['PHASE_1_CONSUMPTION_WATT_OH_ITEM']=''
        values=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        self.assertFalse(values.is_valid_measurement())
        values.phase_1_consumption.value=None
        self.assertTrue(values.is_valid_measurement())

        # NOTE: The value for watt/h is excluded since it is computed after reading from smart meter
        values.phase_1_consumption.value=100
        values.overall_consumption_wh.value=None
        self.assertFalse(values.is_valid_measurement())
    
    def test_conversions(self) -> None:
        values=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        self.assertEqual(len(values.convert_to_item_value_list()), 6)
        self.assertEqual(len(values.convert_to_measurement_item_value_list()), 5)
        self.assertEqual(len(values.convert_to_measurement_value_list()), 5)
        
if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")