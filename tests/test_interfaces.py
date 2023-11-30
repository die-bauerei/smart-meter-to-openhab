import unittest
import logging
import sys

from smart_meter_to_openhab.interfaces import *

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

class TestInterfaces(unittest.TestCase):

    def test_oh_item(self) -> None:
        item=OhItem('')
        self.assertFalse(item)
        item=OhItem('test')
        self.assertTrue(item)
        self.assertEqual(item, 'test')
        self.assertEqual(str(item), 'test')

    def test_classvar(self) -> None:
        self.assertTrue('unit_tests_smart_meter_phase_1_consumption' in SmartMeterValues.oh_item_names())
        self.assertTrue('unit_tests_smart_meter_phase_2_consumption' in SmartMeterValues.oh_item_names())
        self.assertTrue('unit_tests_smart_meter_phase_3_consumption' in SmartMeterValues.oh_item_names())
        self.assertTrue('unit_tests_smart_meter_overall_consumption' in SmartMeterValues.oh_item_names())
        self.assertTrue('unit_tests_smart_meter_electricity_meter' in SmartMeterValues.oh_item_names())
        self.assertTrue('unit_tests_smart_meter_overall_consumption_wh' in ExtendedSmartMeterValues.oh_item_names())

    def test_init(self) -> None:
        values=SmartMeterValues()
        extended_values=ExtendedSmartMeterValues()
        self.assertEqual(values.phase_1_consumption.oh_item, 'unit_tests_smart_meter_phase_1_consumption')
        self.assertEqual(values.phase_2_consumption.oh_item, 'unit_tests_smart_meter_phase_2_consumption')
        self.assertEqual(values.phase_3_consumption.oh_item, 'unit_tests_smart_meter_phase_3_consumption')
        self.assertEqual(values.overall_consumption.oh_item, 'unit_tests_smart_meter_overall_consumption')
        self.assertEqual(extended_values.overall_consumption_wh.oh_item, 'unit_tests_smart_meter_overall_consumption_wh')
        self.assertEqual(values.electricity_meter.oh_item, 'unit_tests_smart_meter_electricity_meter')
        self.assertTrue(all(value is None for value in values.value_list()))
        self.assertTrue(all(value is None for value in extended_values.value_list()))
        self.assertEqual(len(values.value_list()), 5)
        self.assertEqual(len(extended_values.value_list()), 1)

    def test_reset(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        none_values=SmartMeterValues()
        self.assertNotEqual(values, none_values)
        values.reset()
        self.assertEqual(values, none_values)

    def test_creation(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        new_values=SmartMeterValues.create(values.item_value_list())
        self.assertEqual(values, new_values)
        values.phase_1_consumption.value=None
        new_values=SmartMeterValues.create(values.item_value_list())
        self.assertEqual(values, new_values)

    def test_creation_not_all_items(self) -> None:
        oh_item_names : SmartMeterOhItemNames = ('', SmartMeterValues.oh_item_names()[1], 
                                                SmartMeterValues.oh_item_names()[2],
                                                SmartMeterValues.oh_item_names()[3],
                                                SmartMeterValues.oh_item_names()[4])
        values=SmartMeterValues(None, None, None, None, None, oh_item_names)
        values.phase_2_consumption.value=200
        values.phase_3_consumption.value=300
        new_values=SmartMeterValues.create(values.item_value_list(), oh_item_names)
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
        oh_item_names : SmartMeterOhItemNames = ('', SmartMeterValues.oh_item_names()[1], 
                                                SmartMeterValues.oh_item_names()[2],
                                                SmartMeterValues.oh_item_names()[3],
                                                SmartMeterValues.oh_item_names()[4])
        values=SmartMeterValues(100, 200, 300, 600, 2.5, oh_item_names)
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

    def test_shared_oh_items(self) -> None:
        value_1=SmartMeterValues(1, 2, 3, 4, 5)
        value_2=SmartMeterValues(6, 7, 8, 9, 10)
        self.assertEqual(id(value_1.phase_1_consumption.oh_item), id(value_2.phase_1_consumption.oh_item))
        self.assertNotEqual(id(value_1.phase_1_consumption.oh_item), id(value_2.phase_2_consumption.oh_item))
        self.assertNotEqual(id(value_1.phase_1_consumption.value), id(value_2.phase_1_consumption.value))
        
if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")