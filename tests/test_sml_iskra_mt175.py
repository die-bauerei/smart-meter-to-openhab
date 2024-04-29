import unittest
import logging
import sys

import pathlib
test_path = str( pathlib.Path(__file__).parent.absolute() )

from smart_meter_to_openhab.interfaces import SmartMeterValues
from smart_meter_to_openhab.sml_iskra_mt175 import _decode_sml_iskra_mt175_one_way

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging.getLogger(__name__)

class TestSmlIskraMt175(unittest.TestCase):

    def test_sml_dumps(self) -> None:
        with open(test_path+"/data/iskra_mt175_valid.sml", "r") as f:
            valid_value=SmartMeterValues(phase_1_consumption=131, 
                                         phase_2_consumption=19, 
                                         phase_3_consumption=13, 
                                         overall_consumption=163, 
                                         electricity_meter=18999.0194)
            self.assertEqual(valid_value, _decode_sml_iskra_mt175_one_way(f.read()))

        with open(test_path+"/data/iskra_mt175_outlier.sml", "r") as f:
            outlier_value=SmartMeterValues(phase_1_consumption=353, 
                                           phase_2_consumption=0, 
                                           phase_3_consumption=12, 
                                           overall_consumption=0, 
                                           electricity_meter=18998.945)
            self.assertEqual(outlier_value, _decode_sml_iskra_mt175_one_way(f.read()))

        with open(test_path+"/data/iskra_mt175_outlier_2.sml", "r") as f:
            outlier_value=SmartMeterValues(phase_1_consumption=48, 
                                           phase_2_consumption=0, 
                                           phase_3_consumption=14, 
                                           overall_consumption=0, 
                                           electricity_meter=641312586937633.0)
            self.assertEqual(outlier_value, _decode_sml_iskra_mt175_one_way(f.read()))

        with open(test_path+"/data/iskra_mt175_outlier_3.sml", "r") as f:
            outlier_value=SmartMeterValues(phase_1_consumption=46, 
                                           phase_2_consumption=0, 
                                           phase_3_consumption=14, 
                                           overall_consumption=0, 
                                           electricity_meter=74.5534)
            self.assertEqual(outlier_value, _decode_sml_iskra_mt175_one_way(f.read()))

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as e:
        logger.exception("Caught Exception: " + str(e))
    except:
        logger.exception("Caught unknow exception")