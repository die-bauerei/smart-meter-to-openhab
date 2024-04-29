from __future__ import annotations
from dataclasses import dataclass
from typing import List, Any, Union, Tuple, ClassVar, Iterator, Callable
from statistics import mean, median
from abc import ABC, abstractmethod
from functools import cache
import os
from .utils import PersistenceValuesType

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
            # TODO: move this to __post_init__ and raise an exception there
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

    def __iter__(self) -> Iterator[OhItemAndValue]:
        return iter(self._oh_items_and_values)
    
    @abstractmethod
    def is_invalid(self) -> bool:
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        pass
    
    def value_list(self) -> List[Any]:
        # consider only the values that really will be used (oh_item name not empty)
        return [oh_item_value.value for oh_item_value in self._oh_items_and_values  if oh_item_value.oh_item]
    
    def __eq__(self, other) -> bool:
        if isinstance(other, OhItemAndValueContainer):
            return self.value_list() == other.value_list()
        return False
    
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
    
    def is_invalid(self) -> bool:
        number_values=[value for value in self.value_list() if value is not None]
        return (not number_values) or any(value < 0 for value in number_values)
    
    def is_valid(self) -> bool:
        return not self.is_invalid()
    
    def is_inconsistent(self, prev_values : SmartMeterValues) -> bool:
        return not self.is_consistent(prev_values)

    def is_consistent(self, prev_values : SmartMeterValues) -> bool:
        if self.electricity_meter.value is None or prev_values.electricity_meter.value is None:
            return True
        e_meter_unexpected_high = prev_values.electricity_meter.value > 1 and self.electricity_meter.value > prev_values.electricity_meter.value*2
        return self.electricity_meter.value >= prev_values.electricity_meter.value and not e_meter_unexpected_high

    def __repr__(self) -> str:
        return f"L1={self.phase_1_consumption.value} L2={self.phase_2_consumption.value} "\
            f"L3={self.phase_3_consumption.value} Overall={self.overall_consumption.value} E={self.electricity_meter.value}"

    @staticmethod
    @cache
    def oh_item_names() -> SmartMeterOhItemNames:
        return SmartMeterValues._oh_item_names

    @staticmethod    
    def create(values : List[OhItemAndValue], user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None) -> SmartMeterValues:
        value=SmartMeterValues(user_specified_oh_item_names=user_specified_oh_item_names)
        value.assign_values(values)
        return value

    @staticmethod
    def create_mean(values : List[SmartMeterValues], user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None) -> SmartMeterValues:
        return SmartMeterValues.create_avg(values, mean, user_specified_oh_item_names)
    
    @staticmethod
    def create_median(values : List[SmartMeterValues], user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None) -> SmartMeterValues:
        return SmartMeterValues.create_avg(values, median, user_specified_oh_item_names)
    
    @staticmethod
    def create_avg(values : List[SmartMeterValues], operator : Callable[[List[float]], float], 
                   user_specified_oh_item_names : Union[SmartMeterOhItemNames, None] = None ) -> SmartMeterValues:
        smart_meter_values=SmartMeterValues(None, None, None, None, None, user_specified_oh_item_names)
        phase_1_value_list = [value.phase_1_consumption.value for value in values if value.phase_1_consumption.value is not None]
        if phase_1_value_list: 
            smart_meter_values.phase_1_consumption.value = operator(phase_1_value_list)
        phase_2_value_list = [value.phase_2_consumption.value for value in values if value.phase_2_consumption.value is not None]
        if phase_2_value_list: 
            smart_meter_values.phase_2_consumption.value = operator(phase_2_value_list)
        phase_3_value_list = [value.phase_3_consumption.value for value in values if value.phase_3_consumption.value is not None]
        if phase_3_value_list: 
            smart_meter_values.phase_3_consumption.value = operator(phase_3_value_list)
        overall_consumption_value_list = [value.overall_consumption.value for value in values if value.overall_consumption.value is not None]
        if overall_consumption_value_list: 
            smart_meter_values.overall_consumption.value = operator(overall_consumption_value_list)
        electricity_meter_value_list = [value.electricity_meter.value for value in values if value.electricity_meter.value is not None]
        if electricity_meter_value_list: 
            smart_meter_values.electricity_meter.value = operator(electricity_meter_value_list)
        return smart_meter_values

    # NOTE: Use PersistenceValuesType as input to consider that the count of values can potentially be different per item.
    # This could be some data optimization in openhab or similar. Whatever the reason is, we have to support it.
    @staticmethod
    def check_if_updated(pers_values : PersistenceValuesType) -> bool:
        # no consumption is good and considered as updated.
        electricity_meter_values=SmartMeterValues.all_values_for_item(4, pers_values)
        if len(electricity_meter_values) > 1 and all(value == electricity_meter_values[0] for value in electricity_meter_values):
            return True
        
        # for all other cases, at least one value has to be different
        for values in pers_values:
            if any(value != values[0] for value in values):
                return True
        return False
    
    @staticmethod
    def all_values_for_item(oh_item_index : int, pers_values : PersistenceValuesType) -> List[float]:
        if not SmartMeterValues.oh_item_names()[oh_item_index]:
            return []

        pers_value_index=0
        for i in range(oh_item_index):
            if SmartMeterValues.oh_item_names()[i]:
                pers_value_index+=1
        return pers_values[pers_value_index] if pers_value_index < len(pers_values) else []

def create_from_persistence_values(list_values : PersistenceValuesType) -> List[SmartMeterValues]:
    smart_meter_values : List[SmartMeterValues] = []
    valid_items=[item for item in SmartMeterValues.oh_item_names() if item]
    for value_index in range(len(list_values[0]) if list_values else 0):
        item_value_list : List[OhItemAndValue] = []
        for item_index, item in enumerate(valid_items):
            item_value_list.append(OhItemAndValue(item, list_values[item_index][value_index]))
        smart_meter_values.append(SmartMeterValues.create(item_value_list))
    return smart_meter_values

def convert_to_persistence_values(values : List[SmartMeterValues]) -> PersistenceValuesType:
    list_values : PersistenceValuesType = []
    for i in range(len(SmartMeterValues().value_list())):
        list_values.append([])
    for value_set in values:
        for index_value, value in enumerate(value_set.value_list()):
            if SmartMeterValues.oh_item_names()[index_value] and value is not None:
                list_values[index_value].append(value)
    return list_values