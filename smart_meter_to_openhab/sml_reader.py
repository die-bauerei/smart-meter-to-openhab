from time import sleep
from datetime import datetime
from logging import Logger
from typing import List, Tuple
from .sml_iskra_mt175 import SmartMeterReader
from .interfaces import SmartMeterValues, ExtendedSmartMeterValues
from .utils import compute_watt_h

class SmlReader():
    def __init__(self, logger : Logger) -> None:
        self._logger=logger

    def read_avg_from_sml(self, reader : SmartMeterReader, read_count : int,
                          ref_values : SmartMeterValues = SmartMeterValues()) -> SmartMeterValues:
        """Read average data from the smart meter via SML

        Parameters
        ----------
        reader : SmartMeterReader
            interface to get measurements. Could later on be used to read from other smart meters.
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
            values=reader.read(ref_values)
            if values.is_valid():
                 all_values.append(values)
            sleep(1)
        if len(all_values) < read_count:
            self._logger.warning(f"Expected {read_count} valid SML values but only received {len(all_values)}. Returning average value anyway.")
        return SmartMeterValues.create_avg(all_values)
    
    def read_avg_from_sml_and_compute_extended_values(self, reader : SmartMeterReader, read_count : int,
                        ref_values : SmartMeterValues = SmartMeterValues()) -> Tuple[SmartMeterValues, ExtendedSmartMeterValues]:
        """Read average data from the smart meter via SML and compute overall watt hours from overall watt

        Parameters
        ----------
        reader : SmartMeterReader
            interface to get measurements. Could later on be used to read from other smart meters.
        read_count : int
            specifies the number of performed reads that are averaged. Between each read is a sleep of 1 sec
        ref_values : SmartMeterValues
            Values that are used as baseline. If a new read value is 100 times higher as the given reference value, 
            it is considered as outlier and will be ignored.
            
        Returns
        -------
        Tuple[SmartMeterValues, ExtendedSmartMeterValues]
            SmartMeterValues: Contains the data read from the smart meter
            ExtendedSmartMeterValues: Contains extended values like watt hours
        """
        time_start=datetime.now()
        avg_values=self.read_avg_from_sml(reader, read_count, ref_values)
        extended_values=ExtendedSmartMeterValues()
        if avg_values.overall_consumption.value is not None:
            # TODO: in case of an error (service restart, ...) the computed time delta would not be realistic. 
            # A possibility would be to take the timestamp of the last value from openHAB.
            # Even better would be to resolve errors (checkout libsml)
            extended_values.overall_consumption_wh.value=compute_watt_h(avg_values.overall_consumption.value, datetime.now() - time_start)
        return (avg_values, extended_values)