from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer
import time

ea = EthernetAdapter("169.254.199.70", 5025)
k6510 = KeithleyDAQ6510(ea)

channels = [101,102,103]

k6510.set_sense_function("voltage",channels)
k6510.set_voltage_dc_sense_range(channels,10)
k6510.set_voltage_dc_nplc(channels,12)
k6510.set_channels_scan(channels)
k6510.set_scan_count(10)
k6510.set_scan_interval(1)

#print(k6510.get_allchannels_sense_function())

# k6510.reset()
# v = k6510.close_individual_channels(channels)
# v = k6510.config_and_measure_voltage(channels, max_voltage=10, ac=False, nplc=10)





