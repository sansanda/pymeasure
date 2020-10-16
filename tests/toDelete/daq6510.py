from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer
import time

ea = EthernetAdapter("169.254.199.70", 5025)
k6510 = KeithleyDAQ6510(ea)



while (True):
    channels = [1,2,3,4]

    v = k6510.measure_voltage(channels,max_voltage=10, ac=False)
    #v = k6510.close_individual_channels([1,2])

    #print(v)
    time.sleep(1)



