from dataclasses import dataclass
from typing import List, Any, ClassVar
from statistics import mean
import os

# NOTE: This is not a dataclass because of this: #https://www.micahsmith.com/blog/2020/01/dataclasses-mutable-defaults/
class OhItemAndValue():
    def __init__(self, oh_item : str, value : Any = None) -> None:
        self.oh_item = oh_item
        self.value = value

@dataclass
class SmartMeterValues():
    oh_item_names : ClassVar[List[str]] = [
        os.getenv('PHASE_1_CONSUMPTION_OH_ITEM', default=''),
        os.getenv('PHASE_2_CONSUMPTION_OH_ITEM', default=''),
        os.getenv('PHASE_3_CONSUMPTION_OH_ITEM', default=''),
        os.getenv('OVERALL_CONSUMPTION_OH_ITEM', default=''),
        os.getenv('ELECTRICITY_METER_OH_ITEM', default='')]
    phase_1_consumption : OhItemAndValue = OhItemAndValue(oh_item_names[0])
    phase_2_consumption : OhItemAndValue = OhItemAndValue(oh_item_names[1])
    phase_3_consumption : OhItemAndValue = OhItemAndValue(oh_item_names[2])
    overall_consumption : OhItemAndValue = OhItemAndValue(oh_item_names[3])
    electricity_meter : OhItemAndValue = OhItemAndValue(oh_item_names[4])

    def reset(self) -> None:
        self.phase_1_consumption.value = None
        self.phase_2_consumption.value = None
        self.phase_3_consumption.value = None
        self.overall_consumption.value = None
        self.electricity_meter.value = None

    def has_none_value(self) -> bool:
        return any(value is None for value in self.convert_to_value_list())

    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        return [self.phase_1_consumption, self.phase_2_consumption, self.phase_3_consumption,
                self.overall_consumption, self.electricity_meter]
    
    def convert_to_value_list(self) -> List[Any]:
        full_list : List[OhItemAndValue]=self.convert_to_item_value_list()
        return [v.value for v in full_list]

def create_smart_meter_values(values : List[OhItemAndValue]) -> SmartMeterValues:
    smart_meter_values=SmartMeterValues()
    for v in values:
        if v.oh_item == smart_meter_values.phase_1_consumption.oh_item:
            smart_meter_values.phase_1_consumption.value = v.value
        elif v.oh_item == smart_meter_values.phase_2_consumption.oh_item:
            smart_meter_values.phase_2_consumption.value = v.value
        elif v.oh_item == smart_meter_values.phase_3_consumption.oh_item:
            smart_meter_values.phase_3_consumption.value = v.value
        elif v.oh_item == smart_meter_values.overall_consumption.oh_item:
            smart_meter_values.overall_consumption.value = v.value
        elif v.oh_item == smart_meter_values.electricity_meter.oh_item:
            smart_meter_values.electricity_meter.value = v.value
    return smart_meter_values

def create_avg_smart_meter_values(values : List[SmartMeterValues]) -> SmartMeterValues:
    smart_meter_values=SmartMeterValues()
    phase_1_value_list = [value.phase_1_consumption.value for value in values if value.phase_1_consumption.value is not None]
    if phase_1_value_list: 
        smart_meter_values.phase_1_consumption.value = mean(phase_1_value_list)
    phase_2_value_list = [value.phase_2_consumption.value for value in values if value.phase_2_consumption.value is not None]
    if phase_2_value_list: 
        smart_meter_values.phase_2_consumption.value = mean(phase_2_value_list)
    phase_3_value_list = [value.phase_3_consumption.value for value in values if value.phase_3_consumption.value is not None]
    if phase_3_value_list: 
        smart_meter_values.phase_3_consumption.value = mean(phase_3_value_list)
    overall_consumption_value_list = [value.overall_consumption.value for value in values if value.overall_consumption.value is not None]
    if overall_consumption_value_list: 
        smart_meter_values.overall_consumption.value = mean(overall_consumption_value_list)
    electricity_meter_value_list = [value.electricity_meter.value for value in values if value.electricity_meter.value is not None]
    if electricity_meter_value_list: 
        smart_meter_values.electricity_meter.value = mean(electricity_meter_value_list)
    return smart_meter_values