from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer
import time

ea = EthernetAdapter("169.254.199.70", 5025)
k6510 = KeithleyDAQ6510(ea)
channels = [101]

k6510.reset()
k6510.set_sense_function("voltage", channels)
k6510.channels_open_all()
k6510.channels_set_close(channels)
k6510.read()






