from dataclasses import dataclass
from typing import Union, List, Any
import os

class OhItemAndValue():
    def __init__(self, oh_item : Union[str, None], value : Any = None) -> None:
        self.oh_item = oh_item
        self.value = value

#https://www.micahsmith.com/blog/2020/01/dataclasses-mutable-defaults/
@dataclass
class SmartMeterValues():
    phase_1_consumption : OhItemAndValue = OhItemAndValue(oh_item=os.getenv('PHASE_1_CONSUMPTION_OH_ITEM'))
    phase_2_consumption : OhItemAndValue = OhItemAndValue(oh_item=os.getenv('PHASE_2_CONSUMPTION_OH_ITEM'))
    phase_3_consumption : OhItemAndValue = OhItemAndValue(oh_item=os.getenv('PHASE_3_CONSUMPTION_OH_ITEM'))
    overall_consumption : OhItemAndValue = OhItemAndValue(oh_item=os.getenv('OVERALL_CONSUMPTION_OH_ITEM'))
    electricity_meter : OhItemAndValue = OhItemAndValue(oh_item=os.getenv('ELECTRICITY_METER_OH_ITEM'))

    def reset(self) -> None:
        self.phase_1_consumption.value = None
        self.phase_2_consumption.value = None
        self.phase_3_consumption.value = None
        self.overall_consumption.value = None
        self.electricity_meter.value = None

    def convert_to_list(self) -> List[OhItemAndValue]:
        return [self.phase_1_consumption, self.phase_2_consumption, self.phase_3_consumption,
                self.overall_consumption, self.electricity_meter]
    
    def convert_to_oh_item_list(self) -> List[str]:
        full_list : List[OhItemAndValue]=self.convert_to_list()
        return [v.oh_item for v in full_list if v.oh_item]

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