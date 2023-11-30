from __future__ import annotations
from dataclasses import dataclass
from typing import List, Any, Union, Tuple, ClassVar, cast
from statistics import mean
from abc import ABC
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

@dataclass(init=False)
class OhItemAndValue():
    _shared_oh_items : ClassVar[List[OhItem]] = []
    
    _oh_item_index : int
    value : Union[float, None] = None

    def __init__(self, oh_item_name : str, value : Union[float, None] = None) -> None:
        if oh_item_name not in OhItemAndValue._shared_oh_items:
            OhItemAndValue._shared_oh_items.append(OhItem(oh_item_name))
        for oh_item_index, oh_item in enumerate(OhItemAndValue._shared_oh_items):
            if oh_item == oh_item_name:
                self._oh_item_index = oh_item_index
                self.value = value
                break

    @property
    def oh_item(self) -> OhItem:
        return OhItemAndValue._shared_oh_items[self._oh_item_index]

ContainerValuesType = Union[Tuple[Union[float, None], ...], None]
class OhItemAndValueContainer(ABC):
    def __init__(self, oh_item_names : Tuple[str, ...], values : ContainerValuesType = None) -> None:
        if values is not None and len(oh_item_names) != len(values):
            raise ValueError(f"Unable to create OhItemAndValueContainer: Value size mismatch")
        self._oh_items_and_values=[OhItemAndValue(oh_item_names[i], values[i] if values is not None else None) for i in range(len(oh_item_names))]

    def reset(self) -> None:
        for oh_item_value in self._oh_items_and_values:
            oh_item_value.value = None

    def assign_values(self, new_values : List[OhItemAndValue]) -> None:
        for new_value in new_values:
            for this_value in self._oh_items_and_values:
                if this_value.oh_item == new_value.oh_item:
                    this_value.value = new_value.value
                    break
                    
    def item_value_list(self) -> List[OhItemAndValue]:
        return self._oh_items_and_values.copy()

    def is_invalid(self) -> bool:
        return any(oh_item_value.value is None for oh_item_value in self._oh_items_and_values)
    
    def value_list(self) -> List[Any]:
        return [v.value for v in self._oh_items_and_values]
    
    def __eq__(self, other) -> bool:
        if isinstance(other, OhItemAndValueContainer):
            return self._oh_items_and_values == other._oh_items_and_values
        return False
    
    @staticmethod    
    def create_container(values : List[OhItemAndValue], oh_item_names : Tuple[str,...]) -> OhItemAndValueContainer:
        value_container=OhItemAndValueContainer(oh_item_names)
        value_container.assign_values(values)
        return value_container
    
# NOTE: Use a tuple (immutable type) here to prevent changing the values 
SmartMeterOhItemNames = Tuple[str, str, str, str, str]
def _read_smart_meter_env() -> SmartMeterOhItemNames:
    return (os.getenv('PHASE_1_CONSUMPTION_WATT_OH_ITEM', default=''),
            os.getenv('PHASE_2_CONSUMPTION_WATT_OH_ITEM', default=''),
            os.getenv('PHASE_3_CONSUMPTION_WATT_OH_ITEM', default=''),
            os.getenv('OVERALL_CONSUMPTION_WATT_OH_ITEM', default=''),
            os.getenv('ELECTRICITY_METER_KWH_OH_ITEM', default=''))

class SmartMeterValues(OhItemAndValueContainer):
    _oh_item_names : SmartMeterOhItemNames = _read_smart_meter_env()
    
    def __init__(self, phase_1_consumption : Union[float, None] = None, phase_2_consumption : Union[float, None] = None, 
                 phase_3_consumption : Union[float, None] = None, overall_consumption : Union[float, None] = None, 
                 electricity_meter : Union[float, None] = None, 
                 user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None) -> None:
        oh_items = user_specified_oh_item_names if user_specified_oh_item_names is not None else SmartMeterValues._oh_item_names
        super().__init__(oh_items, (phase_1_consumption, phase_2_consumption, phase_3_consumption, overall_consumption, electricity_meter))

    @property
    def phase_1_consumption(self) -> OhItemAndValue:
        return self._oh_items_and_values[0]
    @property
    def phase_2_consumption(self) -> OhItemAndValue:
        return self._oh_items_and_values[1]
    @property
    def phase_3_consumption(self) -> OhItemAndValue:
        return self._oh_items_and_values[2]
    @property
    def overall_consumption(self) -> OhItemAndValue:
        return self._oh_items_and_values[3]
    @property
    def electricity_meter(self) -> OhItemAndValue:
        return self._oh_items_and_values[4]
    
    def __repr__(self) -> str:
        return f"L1={self.phase_1_consumption.value} L2={self.phase_2_consumption.value} "\
            f"L3={self.phase_3_consumption.value} Overall={self.overall_consumption.value} E={self.electricity_meter.value}"

    @staticmethod
    def oh_item_names() -> SmartMeterOhItemNames:
        return SmartMeterValues._oh_item_names

    @staticmethod    
    def create(values : List[OhItemAndValue], user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None) -> SmartMeterValues:
        oh_items = user_specified_oh_item_names if user_specified_oh_item_names is not None else SmartMeterValues.oh_item_names()
        return cast(SmartMeterValues, OhItemAndValueContainer.create_container(values, oh_items))
    
    @staticmethod
    def create_avg(values : List[SmartMeterValues], user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None) -> SmartMeterValues:
        smart_meter_values=SmartMeterValues(None, None, None, None, None, user_specified_oh_item_names)
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

# NOTE: Use a tuple (immutable type) here to prevent changing the values 
ExtendedSmartMeterOhItemNames = Tuple[str]
def _read_extended_smart_meter_env() -> ExtendedSmartMeterOhItemNames:
    return (os.getenv('OVERALL_CONSUMPTION_WH_OH_ITEM', default=''),)

class ExtendedSmartMeterValues(OhItemAndValueContainer):
    _oh_item_names : ExtendedSmartMeterOhItemNames = _read_extended_smart_meter_env()

    def __init__(self, overall_consumption_wh : Union[float, None] = None,
                 user_specified_oh_item_name : Union[ExtendedSmartMeterOhItemNames, None] = None) -> None:
        oh_items = user_specified_oh_item_name if user_specified_oh_item_name is not None else ExtendedSmartMeterValues._oh_item_names
        super().__init__(oh_items, (overall_consumption_wh,))

    @property
    def overall_consumption_wh(self) -> OhItemAndValue:
        return self._oh_items_and_values[0]

    def __repr__(self) -> str:
        return f"Overall(Wh)={self.overall_consumption_wh.value}"

    @staticmethod
    def oh_item_names() -> ExtendedSmartMeterOhItemNames:
        return ExtendedSmartMeterValues._oh_item_names

    @staticmethod    
    def create(values : List[OhItemAndValue], user_specified_oh_item_names : Union[ExtendedSmartMeterOhItemNames, None] = None) -> ExtendedSmartMeterValues:
        oh_items = user_specified_oh_item_names if user_specified_oh_item_names is not None else ExtendedSmartMeterValues.oh_item_names()
        return cast(ExtendedSmartMeterValues, OhItemAndValueContainer.create_container(values, oh_items))