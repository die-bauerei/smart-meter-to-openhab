import serial
from datetime import timedelta, datetime
from logging import Logger
from .interfaces import SmartMeterValues

class SmlReader():
    def __init__(self, serial_port : str, logger : Logger) -> None:
        self._port=serial.Serial(port=serial_port, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self._logger=logger
        self._smart_meter_values = SmartMeterValues()

    def read_from_sml(self, time_out : timedelta = timedelta(minutes=10)) -> SmartMeterValues:
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
        self._smart_meter_values.reset()
        time_start=datetime.now()
        while (datetime.now() - time_start) > time_out:
            input : bytes = self._port.read()
            data += input.hex()          # Convert Bytes to Hex String to use find function for easy parsing

            pos = data.find('1b1b1b1b01010101')        # find start of Frame

            if (pos != -1):
                data = data[pos:]                      # cut trash before start delimiter

            pos = data.find('1b1b1b1b1a')              # find end of Frame

            if (pos != -1) and len(data) >= pos + 16:
                data = data[0:pos + 16]                # cut trash after end delimiter
                
                pos = data.find('070100010800ff') # looking for OBIS Code: 1-0:1.8.0*255 - Energy kWh
                self._smart_meter_values.electricity_meter.value = int(data[pos+36:pos + 52], 16) / 1e4 if pos != -1 else None

                pos = data.find('070100100700ff') # looking for OBIS Code: 1-0:16.7.0*255 - Sum Power L1,L2,L3
                self._smart_meter_values.overall_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                pos = data.find('070100240700ff') # looking for OBIS Code: 1-0:36.7.0*255 - current Power L1
                self._smart_meter_values.phase_1_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                pos = data.find('070100380700ff') # looking for OBIS Code: 1-0:56.7.0*255 - current Power L2
                self._smart_meter_values.phase_2_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                pos = data.find('0701004c0700ff') # looking for OBIS Code: 1-0:76.7.0*255 - current Power L3
                self._smart_meter_values.phase_3_consumption.value = int(data[pos+28:pos+36], 16) if pos != -1 else None

                break
        
        if (datetime.now() - time_start) > time_out:
            self._logger.info(f"Exceeded time out of {time_out} while reading from smart meter.")
                
        return self._smart_meter_values