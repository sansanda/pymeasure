#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import logging
import time

from pymeasure.instruments import Instrument
from enum import IntEnum

from pymeasure.instruments.validators import strict_discrete_set

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Eurotherm2404(Instrument):
    """ Represents the Euro Test High Voltage DC Source model HPP-120-256
    and provides a high-level interface for interacting with the instrument using the
    Euro Test command set (Not SCPI command set).

    .. code-block:: python

        eurotherm2404 = Eurotherm2404('ASRL5::INSTR',
        baud_rate=9600, data_bits=8, write_termination = '\n',read_termination='\n',
        parity=Parity.none)

        print(eurotherm2404.id)
    """
    byteMode = 2  # is the length in bytes of the register (normally holding registers RTU 2 bytes)

    # MODBUS ADDRESSES
    PROCESS_TEMP_ADDR = 0x01
    SELECTED_SETPOINT_VALUE_ADDR = 0x02
    SELECT_SETPOINT_ADRR = 0x0f  # 15
    CURRENTLY_SELECTED_SETPOINT_ADRR = 0x0123  # 291
    SETPOINT1_VALUE_ADDR = 0x18  # 24
    SETPOINT2_VALUE_ADDR = 0x19  # 25
    OUTPUTPOWER_ADDR = 0x03
    MODE_ADDR = 0x0111  # 273
    USER_CALIBRATION_ENABLE_ADDR = 0x6e  # 110
    RESOLUTION_ADDR = 0x3106  # 12550

    # OVEN RATINGS
    MAX_TEMP = 500
    MIN_TEMP = 0
    MIN_OUTPUTPOWER = 0
    MAX_OUTPUTPOWER = 100

    # OVEN WORKING MODES
    MANUAL_MODE = 1
    AUTO_MODE = 0

    # RESOLUTION MODES
    FULL_RESOLUTION = 0
    INTEGER_RESOLUTION = 1

    # OVEN CALIBRATION OPTIONS
    FACTORY_CALIBRATION = 0
    USER_CALIBRATION = 0

    # CONTROLLER CHARACTERISTICS
    NUMBER_OF_SETPOINTS_AVAILABLE = 2

    def __init__(self,
                 adapter,
                 name="Eurotherm2404",
                 address=1,
                 timeout=1000,
                 read_delay=0.1,
                 write_delay=0.1,
                 query_delay=0.1,
                 **kwargs):
        """Initialize the device."""
        super().__init__(
            adapter,
            name,
            write_termination="",
            read_termination="",
            send_end=True,
            includeSCPI=True,
            timeout=timeout,
            **kwargs
        )
        self.address = address
        self.write_delay = write_delay
        self.read_delay = read_delay
        self.query_delay = query_delay
        self.last_write_timestamp = 0.0
        self.last_read_timestamp = 0.0
        self.last_query_timestamp = 0.0

    selected_setpoint = Instrument.control(
        "R," + str(CURRENTLY_SELECTED_SETPOINT_ADRR),
        "W," + str(SELECT_SETPOINT_ADRR) + ",%i",
        """Control the selection of the temperature setpoint for the temperature controller.
        Usually, in standard controllers, only two setpoints are available.
        0 corresponds to SP1 and 1 corresponds to SP2 """,
        validator=strict_discrete_set,
        values=[n for n in range(0, NUMBER_OF_SETPOINTS_AVAILABLE)]
    )

    selected_setpoint_value = Instrument.setting(
        "W," + str(SELECTED_SETPOINT_VALUE_ADDR) + ",%i",
        """Control the selected setpoint of the oven in °C."""
    )

    setpoint1_value = Instrument.measurement(
        "R," + str(SETPOINT1_VALUE_ADDR),
        """Measure the setpoint1 of the oven in °C."""
    )

    setpoint2_value = Instrument.measurement(
        "R," + str(SETPOINT2_VALUE_ADDR),
        """Measure the setpoint2 of the oven in °C."""
    )

    process_temperature = Instrument.measurement(
        "R," + str(PROCESS_TEMP_ADDR),
        """Measure the current oven temperature in °C."""
    )

    automode_enabled = Instrument.setting(
        "W," + str(MODE_ADDR) + ",%i",
        """Control the working mode of the temperature controller.""",
        validator=strict_discrete_set,
        map_values=True,
        values={True: AUTO_MODE, False: MANUAL_MODE}
    )

    output_power = Instrument.measurement(
        "R," + str(OUTPUTPOWER_ADDR),
        """Measure the current oven output power in %."""
    )

    resolution = Instrument.setting(
        "W," + str(RESOLUTION_ADDR),
        """Control the working mode of the temperature controller.""",
        validator=strict_discrete_set,
        map_values=True,
        values={'full': FULL_RESOLUTION, 'integer': INTEGER_RESOLUTION}
    )

    def write(self, command, **kwargs):
        """Overrides Instrument write method for including write_delay time after the parent call
        and write a command to the device.
        :param str command: comma separated string of:
            - the function: read ('R') or write ('W') or 'echo',
            - the address to write to (e.g. '0x106' or '262'),
            - the values (comma separated) to write
            - or the number of elements to read (defaults to 1).
        """

        actual_write_delay = time.time() - self.last_write_timestamp
        time.sleep(max(0, self.write_delay - actual_write_delay))

        function, address, *values = command.split(",")
        function = Functions[function]
        data = [self.address, function]  # 1B device address
        address = int(address, 16) if "x" in address else int(address)
        data.extend(address.to_bytes(2, "big"))  # 2B register address
        if function == Functions.W:
            elements = len(values) * self.byteMode // 2
            data.extend(elements.to_bytes(2, "big"))  # 2B number of elements
            data.append(elements * 2)  # 1B number of bytes to write
            for element in values:
                data.extend(int(element).to_bytes(self.byteMode, "big", signed=True))
        elif function == Functions.R:
            count = int(values[0]) * self.byteMode // 2 if values else self.byteMode // 2
            data.extend(count.to_bytes(2, "big"))  # 2B number of elements to read
        elif function == Functions.ECHO:
            data[-2:] = [0, 0]
            if values:
                data.extend(int(values[0]).to_bytes(2, "big"))  # 2B test data
        data += CRC16(data)
        self.write_bytes(bytes(data))

        self.last_write_timestamp = time.time()

    def read(self, **kwargs):
        """Read response and interpret the number, returning it as a string."""

        actual_read_delay = time.time() - self.last_read_timestamp
        time.sleep(max(0, self.read_delay - actual_read_delay))

        # Slave address, function
        got = self.read_bytes(2)
        if got[1] == Functions.R:
            # length of data to follow
            length = self.read_bytes(1)
            # data length, 2 Byte CRC
            read = self.read_bytes(length[0] + 2)
            if read[-2:] != bytes(CRC16(got + length + read[:-2])):
                raise ConnectionError("Response CRC does not match.")
            return str(int.from_bytes(read[:-2], byteorder="big", signed=True))
        elif got[1] == Functions.W:
            # start address, number elements, CRC; each 2 Bytes long
            got += self.read_bytes(2 + 2 + 2)
            if got[-2:] != bytes(CRC16(got[:-2])):
                raise ConnectionError("Response CRC does not match.")
        elif got[1] == Functions.ECHO:
            # start address 0, data, CRC; each 2B
            got += self.read_bytes(2 + 2 + 2)
            if got[-2:] != bytes(CRC16(got[:-2])):
                raise ConnectionError("Response CRC does not match.")
            return str(int.from_bytes(got[-4:-2], "big"))
        else:  # an error occurred
            # got[1] is functioncode + 0x80
            end = self.read_bytes(3)  # error code and CRC
            errors = {0x02: "Wrong start address.",
                      0x03: "Variable data error.",
                      0x04: "Operation error."}
            if end[0] in errors.keys():
                raise ValueError(errors[end[0]])
            else:
                raise ConnectionError(f"Unknown read error. Received: {got} {end}")

        self.last_read_timestamp = time.time()

    def ask(self, command, query_delay=0):
        """ Overrides Instrument ask method for including query_delay time on parent call.
        :param command: Command string to be sent to the instrument.
        :param query_delay: Delay between writing and reading in seconds.
        :returns: String returned by the device without read_termination.
        """

        return super().ask(command, query_delay if query_delay else self.query_delay)

    def check_set_errors(self):
        """Check for errors after having set a property.

        Called if :code:`check_set_errors=True` is set for that property.
        """
        try:
            self.read()
        except Exception as exc:
            log.exception("Setting a property failed.", exc_info=exc)
            raise
        else:
            return []

    def ping(self, test_data=0):
        """Test the connection sending an integer up to 65535, checks the response."""
        assert int(self.ask(f"ECHO,0,{test_data}")) == test_data


def CRC16(data):
    """Calculate the CRC16 checksum for the data byte array."""
    CRC = 0xFFFF
    for octet in data:
        CRC ^= octet
        for j in range(8):
            lsb = CRC & 0x1  # least significant bit
            CRC = CRC >> 1
            if lsb:
                CRC ^= 0xA001
    return [CRC & 0xFF, CRC >> 8]


class Functions(IntEnum):
    R = 0x03  # Read holding registers
    WRITESINGLE = 0x06  # Write single register
    ECHO = 0x08  # register address has to be 0
    W = 0x10  # Write multiple registers
