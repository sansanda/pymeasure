import sys

from pyvisa.constants import Parity

from .eurotherm2404 import Eurotherm2404


def main() -> int:
    """Test the communication betwwen PC and the temperature controller Eurotherm 2404"""
    e2404 = Eurotherm2404('ASRL5::INSTR',
                          baud_rate=9600, data_bits=8, write_termination='\n',
                          read_termination='\n',
                          parity=Parity.none)
    print(e2404.temperature)
    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
