import serial
import os
from datetime import timedelta, datetime
from logging import Logger
from typing import Protocol, List, Any, Optional
from functools import cached_property
from pathlib import Path
from .interfaces import SmartMeterValues

MIN_REF_VALUE_IN_WATT=50
def _has_outlier(value_list : List[Any], ref_value_list : List[Any]) -> bool:
    for i in range(len(value_list)):
        if value_list[i] is not None and ref_value_list[i] is not None and value_list[i]*0.001 > max(ref_value_list[i], MIN_REF_VALUE_IN_WATT):
            return True
    return False

class SmartMeterReader(Protocol):
    @cached_property
    def default(self) -> SmartMeterValues:
        ...

    @cached_property
    def estimated_max_read_time_in_sec(self) -> int:
        ...
    
    # TODO: this function can already be implemented in an abstract class
    def read(self, ref_values : SmartMeterValues) -> SmartMeterValues:
        ...

# The smart meter supports consumption only. No electricity feed-in support! (German: Zweirichtungszähler)
class SmlIskraMt175OneWay():
    # Data reading will be canceled after this time period.
    #      NOTE: Take care that this is longer then the specified transmission time of your smart meter.
    _read_raw_time_out_in_sec : int = 5
    # try n times to get a valid raw read
    _max_read_attempts : int = 4

    def __init__(self, serial_port : str, logger : Logger, raw_data_dump_dir : Optional[Path] = None) -> None:
        self._port=serial.Serial(baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self._serial_port=serial_port
        self._logger=logger
        self._latest_raw_data=''
        self._raw_data_dump_dir=raw_data_dump_dir
        self._raw_data_dump_invalid_counter=0
        self._raw_data_dump_outlier_counter=0
        # TODO: add a possibility to dump raw data for valid cases aswell (e.g. when logger.debug)
        if self._raw_data_dump_dir:
            os.makedirs(self._raw_data_dump_dir, exist_ok=True)
            self._logger.info(f"Using directory {self._raw_data_dump_dir} for raw data dumps.")

    @cached_property
    def default(self) -> SmartMeterValues:
        return SmartMeterValues(overall_consumption=0, phase_1_consumption=0, phase_2_consumption=0, phase_3_consumption=0)
    
    @cached_property
    def estimated_max_read_time_in_sec(self) -> int:
        return self._read_raw_time_out_in_sec*self._max_read_attempts

    def read(self, ref_values : SmartMeterValues) -> SmartMeterValues:
        """Read data from the smart meter via SML and try to validate them

        Parameters
        ----------
        ref_values : SmartMeterValues
            Values that are used as baseline to detect outliers
        
        Returns
        -------
        SmartMeterValues
            Contains the data read from the smart meter
        """
        ref_value_list=ref_values.value_list()
        values=SmartMeterValues()
        for i in range(self._max_read_attempts):
            values=self._read_raw()
            if values.is_invalid():
                self._logger.info(f"Detected invalid values during SML read. Trying again")
                if self._raw_data_dump_dir:
                    with open(self._raw_data_dump_dir / f"raw_data_dump_invalid_{self._raw_data_dump_invalid_counter}.sml", 'w') as f:
                        f.write(self._latest_raw_data)
                    self._raw_data_dump_invalid_counter+=1
                continue
            value_list=values.value_list()
            if _has_outlier(value_list, ref_value_list):
                self._logger.info(f"Detected unrealistic values during SML read. Trying again")
                if self._raw_data_dump_dir:
                    with open(self._raw_data_dump_dir / f"raw_data_dump_outlier_{self._raw_data_dump_outlier_counter}.sml", 'w') as f:
                        f.write(self._latest_raw_data)
                    self._raw_data_dump_outlier_counter+=1
                continue
            break

        value_list=values.value_list()
        if values.is_invalid() or _has_outlier(value_list, ref_value_list):
            self._logger.warning(f"Unable to read and validate SML data. Ignoring following values: {values}")
            values.reset()

        return values if values.is_valid() else self.default

    def _read_raw(self) -> SmartMeterValues:
        """Read raw data from the smart meter via SML

        Parameters
        ----------
        time_out : timedelta
            Data reading will be canceled after this time period.
            NOTE: Take care that this is longer then the specified transmission time of your smart meter.
        
        Returns
        -------
        SmartMeterValues
            Contains the data read from the smart meter
        """

        def _convert_to_float(pos_begin : int, pos_end : int) -> Optional[float]:
            try:
                return int(self._latest_raw_data[pos_begin:pos_end], 16)
            except Exception as e:
                self._logger.info("Caught Exception in _read_raw.__convert_to_float: " + str(e))
                return None

        self._latest_raw_data = ''
        smart_meter_values=SmartMeterValues()
        try:
            if not self._port.is_open:
                self._port.port=self._serial_port
                self._port.open()
            time_out : timedelta = timedelta(seconds=self._read_raw_time_out_in_sec)
            time_start=datetime.now()
            while (datetime.now() - time_start) <= time_out:
                input : bytes = self._port.read()
                self._latest_raw_data += input.hex() # Convert Bytes to Hex String to use find function for easy parsing

                pos = self._latest_raw_data.find('1b1b1b1b01010101') # find start of Frame

                if (pos != -1):
                    self._latest_raw_data = self._latest_raw_data[pos:] # cut trash before start delimiter

                pos = self._latest_raw_data.find('1b1b1b1b1a')              # find end of Frame

                if (pos != -1) and len(self._latest_raw_data) >= pos + 16:
                    self._latest_raw_data = self._latest_raw_data[0:pos + 16]                # cut trash after end delimiter
                    
                    pos = self._latest_raw_data.find('070100010800ff') # looking for OBIS Code: 1-0:1.8.0*255 - Energy kWh
                    smart_meter_values.electricity_meter.value = _convert_to_float(pos+36, pos+52) if pos != -1 else None
                    if smart_meter_values.electricity_meter.value is not None:
                        smart_meter_values.electricity_meter.value /= 1e4

                    pos = self._latest_raw_data.find('070100100700ff') # looking for OBIS Code: 1-0:16.7.0*255 - Sum Power L1,L2,L3
                    smart_meter_values.overall_consumption.value = _convert_to_float(pos+28, pos+36) if pos != -1 else None

                    pos = self._latest_raw_data.find('070100240700ff') # looking for OBIS Code: 1-0:36.7.0*255 - current Power L1
                    smart_meter_values.phase_1_consumption.value = _convert_to_float(pos+28, pos+36) if pos != -1 else None

                    pos = self._latest_raw_data.find('070100380700ff') # looking for OBIS Code: 1-0:56.7.0*255 - current Power L2
                    smart_meter_values.phase_2_consumption.value = _convert_to_float(pos+28, pos+36) if pos != -1 else None

                    pos = self._latest_raw_data.find('0701004c0700ff') # looking for OBIS Code: 1-0:76.7.0*255 - current Power L3
                    smart_meter_values.phase_3_consumption.value = _convert_to_float(pos+28, pos+36) if pos != -1 else None

                    break
            
            if (datetime.now() - time_start) > time_out:
                self._logger.warning(f"Exceeded time out of {time_out} while reading from smart meter.")
        except serial.SerialException as e:
            self._logger.info("Caught Exception in _read_raw: " + str(e))
            #self._port.close() # TODO: is this needed? 
            smart_meter_values.reset()
        
        return smart_meter_values