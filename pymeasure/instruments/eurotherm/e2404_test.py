import sys
import time

from pyvisa.constants import Parity
from pymeasure.instruments.eurotherm.eurotherm2404 import Eurotherm2404


def main() -> int:
    """Test the communication betwwen PC and the temperature controller Eurotherm 2404"""
    e2404 = Eurotherm2404('ASRL3::INSTR')
    e2404.automode_enabled = False
    e2404.selected_setpoint = 1
    e2404.selected_setpoint_target = 75
    e2404.automode_enabled = True
    # time.sleep(10)
    while True:
        print("Temperature setpoint value: ", e2404.setpoint1_value)
        print("Process temperature: ", e2404.process_temperature_value)
        print("Output power: ", e2404.output_power)
        time.sleep(1)


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
