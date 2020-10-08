from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer

ea = EthernetAdapter("169.254.199.70", 5025)
k2700 = KeithleyDAQ6510(ea)

