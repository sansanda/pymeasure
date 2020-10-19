from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer
import time

ea = EthernetAdapter("169.254.199.70", 5025)
k6510 = KeithleyDAQ6510(ea)




channels = [1,2,3,4]

k6510.get_sense_function(channels)

# k6510.reset()
# v = k6510.close_individual_channels(channels)
# v = k6510.config_and_measure_voltage(channels, max_voltage=10, ac=False, nplc=10)





