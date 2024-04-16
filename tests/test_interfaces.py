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

    def test_init(self) -> None:
        values=SmartMeterValues()
        self.assertEqual(values.phase_1_consumption.oh_item, 'unit_tests_smart_meter_phase_1_consumption')
        self.assertEqual(values.phase_2_consumption.oh_item, 'unit_tests_smart_meter_phase_2_consumption')
        self.assertEqual(values.phase_3_consumption.oh_item, 'unit_tests_smart_meter_phase_3_consumption')
        self.assertEqual(values.overall_consumption.oh_item, 'unit_tests_smart_meter_overall_consumption')
        self.assertEqual(values.electricity_meter.oh_item, 'unit_tests_smart_meter_electricity_meter')
        self.assertTrue(all(value is None for value in values.value_list()))
        self.assertEqual(len(values.value_list()), 5)

        # Unspecified oh items (empty env variable) should NOT be in the value list
        oh_item_names : SmartMeterOhItemNames = ('', '', '', SmartMeterValues.oh_item_names()[3], SmartMeterValues.oh_item_names()[4])
        partial_values=SmartMeterValues(None, None, None, None, None, oh_item_names)
        self.assertTrue(all(partial_value is None for partial_value in partial_values.value_list()))
        self.assertEqual(len(partial_values.value_list()), 2)

    def test_reset(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        none_values=SmartMeterValues()
        self.assertNotEqual(values, none_values)
        values.reset()
        self.assertEqual(values, none_values)

    def test_creation(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        new_values=SmartMeterValues.create(values._oh_items_and_values)
        self.assertEqual(values, new_values)
        values.phase_1_consumption.value=None
        new_values=SmartMeterValues.create(values._oh_items_and_values)
        self.assertEqual(values, new_values)

    def test_creation_not_all_items(self) -> None:
        oh_item_names : SmartMeterOhItemNames = ('', SmartMeterValues.oh_item_names()[1], 
                                                SmartMeterValues.oh_item_names()[2],
                                                SmartMeterValues.oh_item_names()[3],
                                                SmartMeterValues.oh_item_names()[4])
        values=SmartMeterValues(None, None, None, None, None, oh_item_names)
        values.phase_2_consumption.value=200
        values.phase_3_consumption.value=300
        new_values=SmartMeterValues.create(values._oh_items_and_values, oh_item_names)
        self.assertEqual(values, new_values)

    def test_creation_average(self) -> None:
        values_1=SmartMeterValues(100, 200, 300, 600, 2.5)
        values_2=SmartMeterValues(200, 300, 400, 700, 3.5)
        new_values=SmartMeterValues.create_avg([values_1, values_2])
        self.assertEqual(SmartMeterValues(150, 250, 350, 650, 3.0), new_values)

        values_incl_none_1=SmartMeterValues(200, 300, None, 300, None)
        new_values=SmartMeterValues.create_avg([values_1, values_incl_none_1])
        self.assertEqual(SmartMeterValues(150, 250, 300, 450, 2.5), new_values)
        
        values_incl_none_2=SmartMeterValues(100, None, 100, 100, None)
        new_values=SmartMeterValues.create_avg([values_incl_none_1, values_incl_none_2])
        self.assertEqual(SmartMeterValues(150, 300, 100, 200, None), new_values)

    def test_is_invalid(self) -> None:
        values=SmartMeterValues(100, 200, 300, 600, 2.5)
        self.assertFalse(values.is_invalid())
        values.phase_1_consumption.value=None
        self.assertFalse(values.is_invalid())
        values.reset()
        self.assertTrue(values.is_invalid())

        # NOTE: Unspecified values should NOT be tested against None.
        oh_item_names : SmartMeterOhItemNames = ('', SmartMeterValues.oh_item_names()[1], 
                                                SmartMeterValues.oh_item_names()[2],
                                                SmartMeterValues.oh_item_names()[3],
                                                SmartMeterValues.oh_item_names()[4])
        values=SmartMeterValues(100, 200, 300, 600, 2.5, oh_item_names)
        self.assertFalse(values.is_invalid())
        values.phase_1_consumption.value=None
        self.assertFalse(values.is_invalid())

        default_values=SmartMeterValues(overall_consumption=0, phase_1_consumption=0, phase_2_consumption=0, phase_3_consumption=0)
        self.assertFalse(default_values.is_invalid())

        # ALL values have to be positive
        negative_values=SmartMeterValues(1, -2, 3, -4, 5)
        self.assertTrue(negative_values.is_invalid())

    def test_comparison(self) -> None:
        values_1=SmartMeterValues(100, 200, 300, 600, 2.5)
        values_2=SmartMeterValues(100, 200, 300, 600, 2.5)
        self.assertEqual(values_1, values_2)
        values_3=SmartMeterValues(200, 300, 400, 600, 2.5)
        self.assertNotEqual(values_1, values_3)

        # Unspecified oh items (empty env variable) should NOT be used for value comparison
        oh_item_names : SmartMeterOhItemNames = ('', '', '', SmartMeterValues.oh_item_names()[3], SmartMeterValues.oh_item_names()[4])
        all_values_partial_items=SmartMeterValues(1, 2, 3, 4, 5, oh_item_names)
        self.assertEqual(all_values_partial_items, SmartMeterValues(None, None, None, 4, 5, oh_item_names))
        self.assertEqual(all_values_partial_items, SmartMeterValues(10, 20, 30, 4, 5, oh_item_names))
        self.assertNotEqual(all_values_partial_items, SmartMeterValues(10, 20, 30, 40, 5, oh_item_names))

    def test_shared_oh_items(self) -> None:
        value_1=SmartMeterValues(1, 2, 3, 4, 5)
        value_2=SmartMeterValues(6, 7, 8, 9, 10)
        self.assertEqual(id(value_1.phase_1_consumption.oh_item), id(value_2.phase_1_consumption.oh_item))
        self.assertNotEqual(id(value_1.phase_1_consumption.oh_item), id(value_2.phase_2_consumption.oh_item))
        self.assertNotEqual(id(value_1.phase_1_consumption.value), id(value_2.phase_1_consumption.value))

    def test_create_from_persistence_values(self) -> None:
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
        smart_meter_values=create_from_persistence_values(list_values)
        self.assertEqual(smart_meter_values[0], smv_1)
        self.assertEqual(smart_meter_values[1], smv_2)
        self.assertEqual(smart_meter_values[2], smv_3)
        self.assertIsInstance(smart_meter_values[0], SmartMeterValues)
        self.assertIsInstance(smart_meter_values[1], SmartMeterValues)
        self.assertIsInstance(smart_meter_values[2], SmartMeterValues)

        # an empty list has to be supported
        self.assertFalse(create_from_persistence_values([]))

        # input lists of unequal size is not supported
        with self.assertRaises(Exception):
            create_from_persistence_values([[1,2,3],[4,5]])

    def test_convert_to_persistence_values(self) -> None:
        value_1=SmartMeterValues(1, 2, 3, 4, 5)
        value_2=SmartMeterValues(6, 7, 8, 9, 10)
        pers_values : PersistenceValuesType = convert_to_persistence_values([value_1, value_2])
        self.assertEqual(pers_values,[[1,6], [2,7], [3,8], [4,9], [5,10]])

        value_1=SmartMeterValues(1, 2, 3, 4, 5)
        value_2=SmartMeterValues()
        pers_values=convert_to_persistence_values([value_1, value_2])
        self.assertEqual(pers_values,[[1], [2], [3], [4], [5]])

        value_1=SmartMeterValues(1, 2, 3, 4, 5)
        value_2=SmartMeterValues(6, None, None, None, 10)
        pers_values=convert_to_persistence_values([value_1, value_2])
        self.assertEqual(pers_values,[[1,6], [2], [3], [4], [5,10]])

    def test_check_if_updated(self) -> None:
        invalid=SmartMeterValues()
        valid_no_electricity_meter=SmartMeterValues(100, 200, 300, 400, None)
        valid_all_1=SmartMeterValues(100, 200, 300, 400, 500)
        valid_all_2=SmartMeterValues(10, 20, 30, 40, 50)
        valid_partial=SmartMeterValues(electricity_meter=100)
        zeros=SmartMeterValues(0, 0, 0, 0, electricity_meter=100)
        self.assertTrue(invalid.is_invalid())
        self.assertTrue(valid_all_1.is_valid())
        self.assertTrue(valid_all_2.is_valid())
        self.assertTrue(valid_partial.is_valid())
        self.assertTrue(zeros.is_valid())
        self.assertTrue(valid_no_electricity_meter.is_valid())

        self.assertFalse(SmartMeterValues.check_if_updated(convert_to_persistence_values(
            [valid_no_electricity_meter, valid_no_electricity_meter])))
        self.assertFalse(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_no_electricity_meter])))
        self.assertFalse(SmartMeterValues.check_if_updated([]))
        self.assertFalse(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_all_1])))
        self.assertFalse(SmartMeterValues.check_if_updated(convert_to_persistence_values([zeros])))
        self.assertFalse(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_all_1, invalid])))
        self.assertTrue(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_all_1, valid_all_1])))
        self.assertTrue(SmartMeterValues.check_if_updated(convert_to_persistence_values([zeros, zeros])))
        self.assertTrue(SmartMeterValues.check_if_updated(convert_to_persistence_values([zeros, valid_partial])))
        self.assertTrue(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_all_1, valid_all_2])))
        self.assertTrue(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_all_1, zeros])))
        self.assertTrue(SmartMeterValues.check_if_updated(convert_to_persistence_values([valid_all_1, valid_partial])))
        
if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")