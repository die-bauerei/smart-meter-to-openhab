import serial
from datetime import timedelta, datetime
from logging import Logger
from typing import List, Any
from .interfaces import SmartMeterValues, create_avg_smart_meter_values
from .openhab import OpenhabConnection

class SmlReader():
    def __init__(self, serial_port : str, logger : Logger) -> None:
        self._port=serial.Serial(port=serial_port, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self._logger=logger

    def read_from_sml(self, time_out : timedelta = timedelta(seconds=5)) -> SmartMeterValues:
        """Read data from the smart meter via SML

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
        
        if (datetime.now() - time_start) > time_out:
            self._logger.warning(f"Exceeded time out of {time_out} while reading from smart meter.")
        
        return smart_meter_values

    def read_avg_from_sml(self, read_count : int) -> SmartMeterValues:
        """Read data from the smart meter via SML

        Parameters
        ----------
        read_count : int
            specifies the number of performed reads that are averaged
        time_out : timedelta
            Data reading will be canceled after this time period.
            NOTE: Take care that this is longer then the specified transmission time of your smart meter.

        Returns
        -------
        SmartMeterValues
            Contains the data read from the smart meter
        """
        all_values : List[SmartMeterValues] = []
        while(len(all_values) < read_count):
            values = self.read_from_sml()
            if not values.has_none_value(): 
                all_values.append(values)
        return create_avg_smart_meter_values(all_values)

    def read_and_validate_from_sml(self, oh_connection : OpenhabConnection, time_out : timedelta = timedelta(seconds=20)) -> SmartMeterValues:
        def has_outlier(value_list : List[Any], ref_value_list : List[Any]) -> bool:
            for i in range(len(value_list)):
                if ref_value_list[i] is not None and value_list[i]*0.01 > ref_value_list[i]:
                    return True
            return False
        ref_value_list = oh_connection.get_median_from_items(SmartMeterValues.oh_item_names).convert_to_value_list()
        time_start=datetime.now()
        values=SmartMeterValues()
        value_list=values.convert_to_value_list()
        while (datetime.now() - time_start) <= time_out:
            current_values=self.read_from_sml()
            if current_values.has_none_value():
                self._logger.info(f"Detected invalid values during SML read. Trying again")
                continue
            values=current_values
            value_list=values.convert_to_value_list()
            if has_outlier(value_list, ref_value_list):
                self._logger.info(f"Detected unrealistic values during SML read. Trying again")
                continue
            break
        
        if values.has_none_value() or has_outlier(value_list, ref_value_list):
            self._logger.warning(f"Unable to read and validate SML data. Ignoring following values: "\
                f"L1={values.phase_1_consumption.value} L2={values.phase_2_consumption.value} "\
                f"L3={values.phase_3_consumption.value} Overall={values.overall_consumption.value} E={values.electricity_meter.value}")
            values.reset()

        return values