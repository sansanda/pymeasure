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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from pymeasure.test import expected_protocol
from pymeasure.instruments.eurotherm.eurotherm2404 import Eurotherm2404
from pymeasure.instruments.eurotherm.eurotherm2404 import CRC16


def test_working_setpoint():
    """Verify the communication of the working setpoint."""
    with expected_protocol(
            Eurotherm2404,
            [(bytes([1, 16, 1, 35, 0, 1, 2, 0, 1] + CRC16([1, 16, 1, 35, 0, 1, 2, 0, 1])),
              bytes([1, 16, 1, 35, 0, 1] + CRC16([1, 16, 1, 35, 0, 1]))),
             (bytes([1, 3, 0, 5, 0, 1] + CRC16([1, 3, 0, 5, 0, 1])),
              bytes([1, 3, 2, 0, 1] + CRC16([1, 3, 2, 0, 1])))
             ],
    ) as inst:
        inst.working_setpoint_number = 1
        assert inst.working_setpoint_number == 1


def test_resolution():
    """Verify the communication of the resolution."""
    with expected_protocol(
            Eurotherm2404,
            [(bytes([1, 16, 49, 6, 0, 1, 2, 0, 0] + CRC16([1, 16, 49, 6, 0, 1, 2, 0, 0])),
              bytes([1, 16, 49, 6, 0, 1] + CRC16([1, 16, 49, 6, 0, 1])))],
    ) as inst:
        inst.resolution = "full"


def test_automode_enabled():
    """Verify the communication of the automode enabled."""
    with expected_protocol(
            Eurotherm2404,
            [(bytes([1, 16, 1, 17, 0, 1, 2, 0, 0] + CRC16([1, 16, 1, 17, 0, 1, 2, 0, 0])),
              bytes([1, 16, 1, 17, 0, 1] + CRC16([1, 16, 1, 17, 0, 1])))],
    ) as inst:
        inst.automode_enabled = True
