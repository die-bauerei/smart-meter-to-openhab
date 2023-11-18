from time import sleep
from datetime import datetime
from logging import Logger
from typing import List, Any, Callable
from .interfaces import SmartMeterValues, create_avg_smart_meter_values
from .utils import compute_watt_h

MIN_REF_VALUE_IN_WATT=50
def _has_outlier(value_list : List[Any], ref_value_list : List[Any]) -> bool:
    for i in range(len(value_list)):
        if ref_value_list[i] is not None and value_list[i]*0.001 > max(ref_value_list[i], MIN_REF_VALUE_IN_WATT):
            return True
    return False

class SmlReader():
    SmlReadFunction = Callable[..., SmartMeterValues]

    def __init__(self, logger : Logger) -> None:
        self._logger=logger
    
    def read_from_sml(self, read_func : SmlReadFunction, max_read_count : int = 5, 
                      ref_values : SmartMeterValues = SmartMeterValues()) -> SmartMeterValues:
        """Read data from the smart meter via SML and try to validate them

        Parameters
        ----------
        read_func : SmlReadFunction
            Callable to get measurements. Could later on be used to read from other smart meters.
        max_read_count : int
            specifies the number of performed reads to get a valid read
        ref_values : SmartMeterValues
            Values that are used as baseline. If a new read value is 1000 times higher as the given reference value, 
            it is considered as outlier and will be ignored.
        
        Returns
        -------
        SmartMeterValues
            Contains the data read from the smart meter
        """
        ref_value_list=ref_values.convert_to_measurement_value_list()
        values=SmartMeterValues()
        for i in range(max_read_count):
            values=read_func()
            if values.is_valid_measurement():
                self._logger.info(f"Detected invalid values during SML read. Trying again")
                continue
            value_list=values.convert_to_measurement_value_list()
            if _has_outlier(value_list, ref_value_list):
                self._logger.info(f"Detected unrealistic values during SML read. Trying again")
                continue
            break

        value_list=values.convert_to_measurement_value_list()
        if values.is_valid_measurement() or _has_outlier(value_list, ref_value_list):
            self._logger.warning(f"Unable to read and validate SML data. Ignoring following values: "\
                f"L1={values.phase_1_consumption.value} L2={values.phase_2_consumption.value} "\
                f"L3={values.phase_3_consumption.value} Overall={values.overall_consumption.value} "\
                f"Overall(Wh)={values.overall_consumption_wh.value} E={values.electricity_meter.value}")
            values.reset()

        return values

    def read_avg_from_sml(self, read_func : SmlReadFunction, read_count : int, 
                          ref_values : SmartMeterValues = SmartMeterValues()) -> SmartMeterValues:
        """Read average data from the smart meter via SML

        Parameters
        ----------
        read_func : SmlReadFunction
            Callable to get measurements. Could later on be used to read from other smart meters.
        read_count : int
            specifies the number of performed reads that are averaged. Between each read is a sleep of 1 sec
        ref_values : SmartMeterValues
            Values that are used as baseline. If a new read value is 100 times higher as the given reference value, 
            it is considered as outlier and will be ignored.
            
        Returns
        -------
        SmartMeterValues
            Contains the data read from the smart meter
        """
        all_values : List[SmartMeterValues] = []
        for i in range(read_count):
            values=self.read_from_sml(read_func, 5, ref_values)
            if not values.is_valid_measurement():
                 all_values.append(values)
            sleep(1)
        if len(all_values) < read_count:
            self._logger.warning(f"Expected {read_count} valid SML values but only received {len(all_values)}. Returning average value anyway.")
        return create_avg_smart_meter_values(all_values)
    
    def read_avg_from_sml_and_compute_wh(self, read_func : SmlReadFunction, read_count : int, 
                          ref_values : SmartMeterValues = SmartMeterValues()) -> SmartMeterValues:
        """Read average data from the smart meter via SML and compute overall watt hours from overall watt

        Parameters
        ----------
        read_func : SmlReadFunction
            Callable to get measurements. Could later on be used to read from other smart meters.
        read_count : int
            specifies the number of performed reads that are averaged. Between each read is a sleep of 1 sec
        ref_values : SmartMeterValues
            Values that are used as baseline. If a new read value is 100 times higher as the given reference value, 
            it is considered as outlier and will be ignored.
            
        Returns
        -------
        SmartMeterValues
            Contains the data read from the smart meter
        """
        time_start=datetime.now()
        avg_values=self.read_avg_from_sml(read_func, read_count, ref_values)
        if avg_values.overall_consumption.value is not None:
            avg_values.overall_consumption_wh.value=compute_watt_h(avg_values.overall_consumption.value, datetime.now() - time_start)
        return avg_values