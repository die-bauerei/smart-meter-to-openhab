import unittest
import logging
import sys

from smart_meter_to_openhab.interfaces import *
from smart_meter_to_openhab.sml_iskra_mt175 import *

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

def return_smart_meter_values(values : SmartMeterValues) -> SmartMeterValues:
    return values

class TestSml(unittest.TestCase):

    _test_values : List[SmartMeterValues] = [SmartMeterValues(), SmartMeterValues()]
    _function_call_count : int = 0

    class TestReader(SmartMeterReader):
        def __init__(self) -> None:
            super().__init__(logger)
        
        def _read_raw(self) -> SmartMeterValues:
            values=TestSml._test_values[TestSml._function_call_count]
            TestSml._function_call_count+=1
            return values

    _test_reader=TestReader()

    @staticmethod
    def _return_test_values() -> SmartMeterValues:
        values=TestSml._test_values[TestSml._function_call_count]
        TestSml._function_call_count+=1
        return values

    def test_read(self) -> None:
        TestSml._function_call_count=0
        TestSml._test_values[0]=SmartMeterValues(100, 200, 300, 600, 2.5)
        read_values=self._test_reader.read_avg(read_count=1)
        self.assertEqual(TestSml._test_values[0], read_values)

        # check for single invalid (None) value. The other values should stay valid
        TestSml._function_call_count=0
        TestSml._test_values[0].phase_1_consumption.value=None
        read_values=self._test_reader.read_avg(read_count=1)
        self.assertIsNone(read_values.phase_1_consumption.value)
        self.assertEqual(TestSml._test_values[0], read_values)

    def test_read_with_prev_values(self) -> None:
        TestSml._function_call_count=0
        TestSml._test_values[0]=SmartMeterValues(100, 200, 300, 600, 60)
        SmartMeterReader._prev_avg_values=SmartMeterValues(50, 50, 50, 50, 50)
        read_values=self._test_reader.read_avg(read_count=1)
        self.assertEqual(TestSml._test_values[0], read_values)

        # If there is an outlier, all return values should be None
        TestSml._function_call_count=0
        TestSml._test_values[0].electricity_meter.value=1000000
        read_values=self._test_reader.read_avg(read_count=1)
        self.assertTrue(all(value is None for value in read_values.value_list()))

    def test_read_avg(self) -> None:
        TestSml._function_call_count=0
        TestSml._test_values[0]=SmartMeterValues(100, 200, 300, 600, 2.5)
        TestSml._test_values[1]=SmartMeterValues(200, 300, 400, 700, 4.5)
        read_values=self._test_reader.read_avg(read_count=2)
        self.assertEqual(SmartMeterValues(150, 250, 350, 650, 3.5), read_values)

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")