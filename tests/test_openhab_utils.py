import unittest
import logging
import sys

from smart_meter_to_openhab.interfaces import SmartMeterValues
from smart_meter_to_openhab.openhab import _convert_list_to_smart_meter_values, _check_if_updated

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

class TestOpenhabUtils(unittest.TestCase):

    def test_convert_list_to_smart_meter_values(self) -> None:
        oh_item_names=SmartMeterValues.oh_item_names()
        smv_1=SmartMeterValues(1, 10, 100, 1000, 10000)
        smv_1_value_list=smv_1.value_list()
        smv_2=SmartMeterValues(2, 20, 200, 2000, 20000)
        smv_2_value_list=smv_2.value_list()
        smv_3=SmartMeterValues(3, 30, 300, 3000, 30000)
        smv_3_value_list=smv_3.value_list()

        list_values=[[smv_1_value_list[0],smv_2_value_list[0],smv_3_value_list[0]], 
                     [smv_1_value_list[1],smv_2_value_list[1],smv_3_value_list[1]], 
                     [smv_1_value_list[2],smv_2_value_list[2],smv_3_value_list[2]], 
                     [smv_1_value_list[3],smv_2_value_list[3],smv_3_value_list[3]], 
                     [smv_1_value_list[4],smv_2_value_list[4],smv_3_value_list[4]]]
        smart_meter_values=_convert_list_to_smart_meter_values(oh_item_names, list_values)
        self.assertEqual(smart_meter_values[0], smv_1)
        self.assertEqual(smart_meter_values[1], smv_2)
        self.assertEqual(smart_meter_values[2], smv_3)
        self.assertIsInstance(smart_meter_values[0], SmartMeterValues)
        self.assertIsInstance(smart_meter_values[1], SmartMeterValues)
        self.assertIsInstance(smart_meter_values[2], SmartMeterValues)

        # an empty list has to be supported
        self.assertFalse(_convert_list_to_smart_meter_values(oh_item_names, []))

        # input lists of unequal size is not supported
        with self.assertRaises(Exception):
            _convert_list_to_smart_meter_values(oh_item_names, [[1,2,3],[4,5]])

    '''
    TODO: reactivate this test
    def test_check_if_updated(self) -> None:
        invalid=SmartMeterValues()
        valid_all_1=SmartMeterValues(100, 200, 300, 400, 500)
        valid_all_2=SmartMeterValues(10, 20, 30, 40, 50)
        valid_partial=SmartMeterValues(electricity_meter=100)
        zeros=SmartMeterValues(0, 0, 0, 0, electricity_meter=100)
        self.assertTrue(invalid.is_invalid())
        self.assertTrue(valid_all_1.is_valid())
        self.assertTrue(valid_all_2.is_valid())
        self.assertTrue(valid_partial.is_valid())

        self.assertFalse(_check_if_updated(values=[valid_all_1, invalid]))
        self.assertFalse(_check_if_updated(values=[valid_all_1, valid_all_1]))
        self.assertFalse(_check_if_updated([]))
        self.assertFalse(_check_if_updated(values=[valid_all_1]))
        self.assertFalse(_check_if_updated(values=[zeros]))
        self.assertTrue(_check_if_updated(values=[zeros, zeros]))
        self.assertTrue(_check_if_updated(values=[valid_all_1, valid_all_2]))
        self.assertTrue(_check_if_updated(values=[valid_all_1, zeros]))
        self.assertTrue(_check_if_updated(values=[valid_all_1, valid_partial]))
    '''
        
if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")