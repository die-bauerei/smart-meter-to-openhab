import serial
from time import sleep
from datetime import timedelta, datetime
from logging import Logger
from typing import List, Any
from .interfaces import SmartMeterValues, create_avg_smart_meter_values

MIN_REF_VALUE_IN_WATT=50
def _has_outlier(value_list : List[Any], ref_value_list : List[Any]) -> bool:
    for i in range(len(value_list)):
        if ref_value_list[i] is not None and value_list[i]*0.001 > max(ref_value_list[i], MIN_REF_VALUE_IN_WATT):
            return True
    return False

class SmlReader():
    def __init__(self, serial_port : str, logger : Logger) -> None:
        self._port=serial.Serial(port=serial_port, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self._logger=logger

    def read_raw_from_sml(self, time_out : timedelta = timedelta(seconds=5)) -> SmartMeterValues:
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
        data = ''
        smart_meter_values=SmartMeterValues()
        time_start=datetime.now()
        try:
            while (datetime.now() - time_start) <= time_out:
                input : bytes = self._port.read()
                data += input.hex()          # Convert Bytes to Hex String to use find function for easy parsing

                pos = data.find('1b1b1b1b01010101')        # find start of Frame

                if (pos != -1):
                    data = data[pos:]                      # cut trash before start delimiter

                pos = data.find('1b1b1b1b1a')              # find end of Frame

                if (pos != -1) and len(data) >= pos + 16:
                    data = data[0:pos + 16]                # cut trash after end delimiter
                    
                    pos = data.find('070100010800ff') # looking for OBIS Code: 1-0:1.8.0*255 - Energy kWh
                    smart_meter_values.electricity_meter.value = int(data[pos+36:pos + 52], 16) / 1e4 if pos != -1 else None

                    pos = data.find('070100100700ff') # looking for OBIS Code: 1-0:16.7.0*255 - Sum Power L1,L2,L3
                    smart_meter_values.overall_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                    pos = data.find('070100240700ff') # looking for OBIS Code: 1-0:36.7.0*255 - current Power L1
                    smart_meter_values.phase_1_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                    pos = data.find('070100380700ff') # looking for OBIS Code: 1-0:56.7.0*255 - current Power L2
                    smart_meter_values.phase_2_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                    pos = data.find('0701004c0700ff') # looking for OBIS Code: 1-0:76.7.0*255 - current Power L3
                    smart_meter_values.phase_3_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                    break
        except serial.SerialException as e:
            self._logger.warning("Caught Exception: " + str(e))
            self._logger.warning("Returning None values.")
            self._port.close()
            sleep(5)
            self._port.open()
            smart_meter_values.reset()
        
        if (datetime.now() - time_start) > time_out:
            self._logger.warning(f"Exceeded time out of {time_out} while reading from smart meter.")
        
        return smart_meter_values
    
    def read_from_sml(self, max_read_count : int = 5, ref_values : SmartMeterValues = SmartMeterValues()) -> SmartMeterValues:
        """Read data from the smart meter via SML and try to validate them

        Parameters
        ----------
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
        ref_value_list=ref_values.convert_to_value_list()
        values=SmartMeterValues()
        for i in range(max_read_count):
            values=self.read_raw_from_sml()
            if values.has_none_value():
                self._logger.info(f"Detected invalid values during SML read. Trying again")
                continue
            value_list=values.convert_to_value_list()
            if _has_outlier(value_list, ref_value_list):
                self._logger.info(f"Detected unrealistic values during SML read. Trying again")
                continue
            break

        value_list=values.convert_to_value_list()
        if values.has_none_value() or _has_outlier(value_list, ref_value_list):
            self._logger.warning(f"Unable to read and validate SML data. Ignoring following values: "\
                f"L1={values.phase_1_consumption.value} L2={values.phase_2_consumption.value} "\
                f"L3={values.phase_3_consumption.value} Overall={values.overall_consumption.value} E={values.electricity_meter.value}")
            values.reset()

        return values

    def read_avg_from_sml(self, read_count : int, ref_values : SmartMeterValues = SmartMeterValues()) -> SmartMeterValues:
        """Read average data from the smart meter via SML

        Parameters
        ----------
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
            values=self.read_from_sml(5, ref_values)
            if not values.has_none_value():
                 all_values.append(values)
            sleep(1)
        if len(all_values) < read_count:
            self._logger.warning(f"Expected {read_count} valid SML values but only received {len(all_values)}. Returning average value anyway.")
        return create_avg_smart_meter_values(all_values)