from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer

ea = EthernetAdapter("169.254.199.70", 5025)
k2700 = KeithleyDAQ6510(ea)

import time

#k2700.reset()
#k2700.open_individual_channels('all')
#k2700.close_individual_channels(2)

while (True):
    v = k2700.measure_voltage(10)
    print(v)
    time.sleep(1)



