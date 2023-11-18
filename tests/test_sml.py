import unittest
import logging
import sys
import os

from pathlib import Path
package_path=Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(package_path))
from dotenv import load_dotenv
if os.path.isfile(f"{package_path}/.env"):
    load_dotenv(dotenv_path=f"{package_path}/.env")
from smart_meter_to_openhab.interfaces import *
from smart_meter_to_openhab.sml_reader import *

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

def return_smart_meter_values(values : SmartMeterValues) -> SmartMeterValues:
    return values

class TestSml(unittest.TestCase):

    _test_values : List[SmartMeterValues] = [SmartMeterValues(), SmartMeterValues()]
    _function_call_count : int = 0

    @staticmethod
    def _return_test_values() -> SmartMeterValues:
        values=TestSml._test_values[TestSml._function_call_count]
        TestSml._function_call_count+=TestSml._function_call_count
        return values

    def test_read(self) -> None:
        TestSml._function_call_count=0
        TestSml._test_values[0]=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        reader=SmlReader(logger)
        read_values=reader.read_from_sml(read_func=TestSml._return_test_values, max_read_count=1)
        self.assertEqual(TestSml._test_values[0], read_values)
        # If there is at least one invalid (None) value, all returned values should be None
        TestSml._function_call_count=0
        TestSml._test_values[0].phase_1_consumption.value=None
        read_values=reader.read_from_sml(read_func=TestSml._return_test_values, max_read_count=1)
        self.assertTrue(all(value is None for value in read_values.convert_to_measurement_value_list()))

    def test_read_with_ref_values(self) -> None:
        TestSml._function_call_count=0
        TestSml._test_values[0]=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        reader=SmlReader(logger)
        ref_values=SmartMeterValues.create(50, 50, 50, 50, 50, 50)
        read_values=reader.read_from_sml(read_func=TestSml._return_test_values, max_read_count=1, ref_values=ref_values)
        self.assertEqual(TestSml._test_values[0], read_values)
        # If there is an outlier, all return values should be None
        TestSml._function_call_count=0
        TestSml._test_values[0].phase_1_consumption.value=1000000
        read_values=reader.read_from_sml(read_func=TestSml._return_test_values, max_read_count=1, ref_values=ref_values)
        self.assertTrue(all(value is None for value in read_values.convert_to_measurement_value_list()))

    def test_read_avg(self) -> None:
        TestSml._function_call_count=0
        TestSml._test_values[0]=SmartMeterValues.create(100, 200, 300, 600, 0.6, 2.5)
        TestSml._test_values[1]=SmartMeterValues.create(200, 300, 400, 700, 1.2, 4.5)
        reader=SmlReader(logger)
        read_values=reader.read_avg_from_sml(read_func=TestSml._return_test_values, read_count=1)
        self.assertEqual(SmartMeterValues.create(150, 250, 350, 650, 0.9, 3.5), read_values)

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")