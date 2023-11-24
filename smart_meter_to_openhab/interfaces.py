from __future__ import annotations
from dataclasses import dataclass
from typing import List, Any, Union, Tuple
from statistics import mean
from abc import ABC, abstractmethod
import os

@dataclass(frozen=True, eq=False)
class OhItem():
    oh_item : str
    def __eq__(self, other) -> bool:
        if isinstance(other, OhItem):
            return self.oh_item == other.oh_item
        elif isinstance(other, str):
            return self.oh_item == other
        return False
    
    def __str__(self) -> str:
        return self.oh_item
    
    def __bool__(self) -> bool:
        return bool(self.oh_item)

@dataclass
class OhItemAndValue():
    oh_item : OhItem
    value : Union[float, None] = None

class OhItemAndValueContainer(ABC):
    @abstractmethod
    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        pass

    def is_invalid(self) -> bool:
        return any(value is None for value in self.convert_to_value_list())
    
    def convert_to_value_list(self) -> List[Any]:
        full_list : List[OhItemAndValue]=self.convert_to_item_value_list()
        return [v.value for v in full_list]
    
    def __eq__(self, other) -> bool:
        if isinstance(other, OhItemAndValueContainer):
            return self.convert_to_item_value_list() == other.convert_to_item_value_list()
        return False

# NOTE: Use a tuple (immutable type) here to prevent changing the values 
SmartMeterOhItems = Tuple[OhItem, OhItem, OhItem, OhItem, OhItem]
def _read_smart_meter_env() -> SmartMeterOhItems:
    return (OhItem(os.getenv('PHASE_1_CONSUMPTION_WATT_OH_ITEM', default='')),
            OhItem(os.getenv('PHASE_2_CONSUMPTION_WATT_OH_ITEM', default='')),
            OhItem(os.getenv('PHASE_3_CONSUMPTION_WATT_OH_ITEM', default='')),
            OhItem(os.getenv('OVERALL_CONSUMPTION_WATT_OH_ITEM', default='')),
            OhItem(os.getenv('ELECTRICITY_METER_KWH_OH_ITEM', default='')))

class SmartMeterValues(OhItemAndValueContainer):
    _oh_items : SmartMeterOhItems = _read_smart_meter_env()
    
    def __init__(self, phase_1_consumption : Union[float, None] = None, phase_2_consumption : Union[float, None] = None, 
                 phase_3_consumption : Union[float, None] = None, overall_consumption : Union[float, None] = None, 
                 electricity_meter : Union[float, None] = None, 
                 user_specified_oh_items : Union[SmartMeterOhItems, None] = None) -> None:
        oh_items = user_specified_oh_items if user_specified_oh_items is not None else SmartMeterValues._oh_items
        self.phase_1_consumption = OhItemAndValue(oh_items[0], phase_1_consumption)
        self.phase_2_consumption = OhItemAndValue(oh_items[1], phase_2_consumption)
        self.phase_3_consumption = OhItemAndValue(oh_items[2], phase_3_consumption)
        self.overall_consumption = OhItemAndValue(oh_items[3], overall_consumption)
        self.electricity_meter = OhItemAndValue(oh_items[4], electricity_meter)

    def reset(self) -> None:
        self.phase_1_consumption.value = None
        self.phase_2_consumption.value = None
        self.phase_3_consumption.value = None
        self.overall_consumption.value = None
        self.electricity_meter.value = None

    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        return [self.phase_1_consumption, self.phase_2_consumption, self.phase_3_consumption,
                self.overall_consumption, self.electricity_meter]
    
    def __repr__(self) -> str:
        return f"L1={self.phase_1_consumption.value} L2={self.phase_2_consumption.value} "\
            f"L3={self.phase_3_consumption.value} Overall={self.overall_consumption.value} E={self.electricity_meter.value}"

    @staticmethod    
    def create(values : List[OhItemAndValue]) -> SmartMeterValues:
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
    
    @staticmethod
    def create_avg(values : List[SmartMeterValues]) -> SmartMeterValues:
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

def _read_extended_smart_meter_env() -> OhItem:
    return OhItem(os.getenv('OVERALL_CONSUMPTION_WH_OH_ITEM', default=''))

class ExtendedSmartMeterValues(OhItemAndValueContainer):
    _oh_item : OhItem = _read_extended_smart_meter_env()

    def __init__(self, overall_consumption_wh : Union[float, None] = None,
                 user_specified_oh_item : Union[OhItem, None] = None) -> None:
        oh_item = user_specified_oh_item if user_specified_oh_item is not None else ExtendedSmartMeterValues._oh_item
        self.overall_consumption_wh = OhItemAndValue(oh_item, overall_consumption_wh)

    def convert_to_item_value_list(self) -> List[OhItemAndValue]:
        return [self.overall_consumption_wh]
    
    def __repr__(self) -> str:
        return f"Overall(Wh)={self.overall_consumption_wh.value}"

    @staticmethod    
    def create(values : List[OhItemAndValue]) -> ExtendedSmartMeterValues:
        extended_values=ExtendedSmartMeterValues()
        for v in values:
            if v.oh_item == extended_values.overall_consumption_wh.oh_item:
                extended_values.overall_consumption_wh.value = v.value
        return extended_values