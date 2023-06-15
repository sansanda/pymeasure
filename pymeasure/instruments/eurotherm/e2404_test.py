import sys

from pyvisa.constants import Parity
from pymeasure.instruments.eurotherm.eurotherm2404 import Eurotherm2404


def main() -> int:
    """Test the communication betwwen PC and the temperature controller Eurotherm 2404"""
    e2404 = Eurotherm2404('ASRL3::INSTR')
    print(e2404.temperature)
    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
