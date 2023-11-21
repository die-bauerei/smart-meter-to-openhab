from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any, ClassVar
from statistics import mean
from abc import ABC, abstractmethod
import os

@dataclass
class OhItemAndValue():
    def __init__(self, oh_item : str, value : Any = None) -> None:
        self.oh_item = oh_item
        self.value = value

class OhItemAndValueContainer(ABC):
    @abstractmethod
    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        pass

    def is_invalid(self) -> bool:
        return any(value is None for value in self.convert_to_value_list())
    
    def convert_to_value_list(self) -> List[Any]:
        full_list : List[OhItemAndValue]=self.convert_to_item_value_list()
        return [v.value for v in full_list]

@dataclass
class SmartMeterValues(OhItemAndValueContainer):
    oh_item_names : ClassVar[List[str]] = [
        os.getenv('PHASE_1_CONSUMPTION_WATT_OH_ITEM', default=''),
        os.getenv('PHASE_2_CONSUMPTION_WATT_OH_ITEM', default=''),
        os.getenv('PHASE_3_CONSUMPTION_WATT_OH_ITEM', default=''),
        os.getenv('OVERALL_CONSUMPTION_WATT_OH_ITEM', default=''),
        os.getenv('ELECTRICITY_METER_KWH_OH_ITEM', default='')]
    
    # NOTE: If you would not use a default_factory here, mutable objects would be created which are shared by all instances of the class
    # https://stackoverflow.com/questions/62852942/python-dataclasses-dataclass-reference-to-variable-instead-of-instance-variable
    # https://www.micahsmith.com/blog/2020/01/dataclasses-mutable-defaults/
    phase_1_consumption : OhItemAndValue = field(default_factory=lambda:OhItemAndValue(SmartMeterValues.oh_item_names[0]))
    phase_2_consumption : OhItemAndValue = field(default_factory=lambda:OhItemAndValue(SmartMeterValues.oh_item_names[1]))
    phase_3_consumption : OhItemAndValue = field(default_factory=lambda:OhItemAndValue(SmartMeterValues.oh_item_names[2]))
    overall_consumption : OhItemAndValue = field(default_factory=lambda:OhItemAndValue(SmartMeterValues.oh_item_names[3]))
    electricity_meter : OhItemAndValue = field(default_factory=lambda:OhItemAndValue(SmartMeterValues.oh_item_names[4]))

    def reset(self) -> None:
        self.phase_1_consumption.value = None
        self.phase_2_consumption.value = None
        self.phase_3_consumption.value = None
        self.overall_consumption.value = None
        self.electricity_meter.value = None

    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        return [self.phase_1_consumption, self.phase_2_consumption, self.phase_3_consumption,
                self.overall_consumption, self.electricity_meter]

    @staticmethod    
    def create(phase_1_consumption : float, phase_2_consumption : float, phase_3_consumption : float,
                    overall_consumption : float, electricity_meter : float) -> SmartMeterValues:
        values=SmartMeterValues()
        values.phase_1_consumption.value = phase_1_consumption
        values.phase_2_consumption.value = phase_2_consumption
        values.phase_3_consumption.value = phase_3_consumption
        values.overall_consumption.value = overall_consumption
        values.electricity_meter.value = electricity_meter
        return values

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

@dataclass
class ExtendedSmartMeterValues(OhItemAndValueContainer):
    oh_item_names : ClassVar[List[str]] = [os.getenv('OVERALL_CONSUMPTION_WH_OH_ITEM', default='')]
    overall_consumption_wh : OhItemAndValue = field(default_factory=lambda:OhItemAndValue(ExtendedSmartMeterValues.oh_item_names[0]))
    
    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        return [self.overall_consumption_wh]
    
    @staticmethod    
    def create(overall_consumption_wh : float) -> ExtendedSmartMeterValues:
        values=ExtendedSmartMeterValues()
        values.overall_consumption_wh.value = overall_consumption_wh
        return values
    
def create_extended_smart_meter_values(values : List[OhItemAndValue]) -> ExtendedSmartMeterValues:
    extended_values=ExtendedSmartMeterValues()
    for v in values:
        if v.oh_item == extended_values.overall_consumption_wh.oh_item:
            extended_values.overall_consumption_wh.value = v.value
    return extended_values