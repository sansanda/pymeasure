from pymeasure.adapters.ethernet import EthernetAdapter
from pymeasure.instruments.keithley.keithleyDAQ6510 import KeithleyDAQ6510, KeithleyBuffer
import time

dc_channels = [101, 102, 103]
temp_channels = [104]

ea = EthernetAdapter("169.254.199.70", 5025)
k6510 = KeithleyDAQ6510(ea)

k6510.reset()
k6510.set_sense_function("voltage", dc_channels)
k6510.set_sense_function("temperature", temp_channels)
k6510.set_sense_temperature_nplc(10,temp_channels)
k6510.set_sense_transducer("TCouple",temp_channels)
k6510.set_sense_temperature_themocouple_type('K',temp_channels)
# k6510.set_sense_temperature_rtdfour_type("PT100",temp_channels)
k6510.set_sense_temperature_units("CELSius",temp_channels)
k6510.set_voltage_dc_sense_range(10, dc_channels )
k6510.set_sense_voltage_dc_nplc(12, dc_channels)
k6510.create_scan(dc_channels)
k6510.add_channels_to_scan(temp_channels)
k6510.set_scan_count(10)
k6510.set_scan_interval(1)
k6510.set_scan_mode('USED')
k6510.set_scan_start_stimulus('COMMand')
k6510.enable_scan_restart('OFF')

#print("****",k6510.get_scan_count_step(),"****")


#print(k6510.get_allchannels_sense_function())

# k6510.reset()
# v = k6510.close_individual_channels(channels)
# v = k6510.config_and_measure_voltage(channels, max_voltage=10, ac=False, nplc=10)





