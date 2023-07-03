import sys
import time

from pyvisa.constants import Parity
from pymeasure.instruments.eurotherm.eurotherm2404 import Eurotherm2404
from pymeasure.instruments.eurotherm.eurotherm2404 import CRC16


def main() -> int:
    """Test the communication betwwen PC and the temperature controller Eurotherm 2404"""
    e2404 = Eurotherm2404('ASRL1::INSTR')
    e2404.automode_enabled = False
    e2404.setpoint2_value = 0
    e2404.selected_setpoint_number = 1  # 0 is the setpoint1
    e2404.automode_enabled = True

    update_oven_temperaure_period = 120  # seconds
    sampling_period = 1  # seconds
    temperature_ramp = [30, 40, 50, 60, 70, 80, 90, 100, 0]  # ºC

    # Oven ramp
    for temp_value in temperature_ramp:
        t = 0
        e2404.target_setpoint_value = temp_value
        while t < update_oven_temperaure_period:
            print("Process temperature: ", e2404.process_temperature_value)
            print("Output power: ", e2404.output_power)
            time.sleep(sampling_period)
            t = t + 1


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
