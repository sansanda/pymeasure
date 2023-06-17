import sys

from pyvisa.constants import Parity
from pymeasure.instruments.eurotherm.eurotherm2404 import Eurotherm2404


def main() -> int:
    """Test the communication betwwen PC and the temperature controller Eurotherm 2404"""
    e2404 = Eurotherm2404('ASRL3::INSTR')
    e2404.automode_enabled = False
    e2404.temperature_setpoint_selection = 0
    e2404.temperature_setpoint = 50
    e2404.automode_enabled = True
    while True:
        print("Temperature setpoint value: ", e2404.temperature_setpoint1)
        print("Process temperature: ", e2404.process_temperature)
        print("Output power: ", e2404.output_power)

    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
