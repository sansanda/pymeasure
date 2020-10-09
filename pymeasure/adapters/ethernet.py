#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2020 PyMeasure Developers
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

import logging

import socket
import numpy as np
import os
import sys

from .adapter import Adapter

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class EthernetAdapter(Adapter):
    """ Adapter class for using the Python socket package to allow
    tcp/ip communication to instrument

    :param ip_address: ip address
    :param port: Socket port
    :param kwargs: Any valid key-word argument for socket.socket
    """

    def __init__(self, ip_address, port, **kwargs):
        self.connection = socket.socket()
        self.connection.settimeout(5)  # 5 seconds
        try:
            if isinstance(port, int) and isinstance(ip_address, str):
                self.connection.connect((ip_address, port))
            else:
                self.connection.connect(("127.0.0.1", 5000))
        except socket.error:
            print('Ethernet connection error')
            self.connection.close()
            sys.exit(1)
        finally:
            pass

        # if not self.sendPing(ip_address):
        #     sys.exit(1)

    def __del__(self):
        """ Ensures the connection is closed upon deletion
        """
        self.connection.close()

    def write(self, command):
        """ Sends a command to the instrument

        :param command: SCPI command string to be sent to the instrument
        """
        self.connection.send(command.encode())  # encode added for Python 3

    def read(self):
        """ Reads until the buffer is empty and returns the resulting
        ASCII respone

        :returns: String ASCII response of the instrument.
        """
        resp = self.connection.recv(1024).decode()
        return resp

    def ask(self, command):
        """ Writes the command to the instrument and returns the resulting
        ASCII response

        :param command: SCPI command string to be sent to the instrument
        :returns: String ASCII response of the instrument
        """
        self.connection.send(command.encode())
        return self.connection.recv(1024).decode()

    def binary_values(self, command, header_bytes=0, dtype=np.float32):
        """ Returns a numpy array from a query for binary data 

        :param command: SCPI command to be sent to the instrument
        :param header_bytes: Integer number of bytes to ignore in header
        :param dtype: The NumPy data type to format the values with
        :returns: NumPy array of values
        """
        self.connection.send(command.encode())
        binary = self.connection.recv(1024).decode()
        header, data = binary[:header_bytes], binary[header_bytes:]
        return np.fromstring(data, dtype=dtype)

    def sendPing(self, hostIp):
        response = os.system("ping -c 1 " + hostIp)

        # and then check the response...
        return response == 0

    def __repr__(self):
        return "<EthernetAdapter(sockname='%s')>" % str(self.connection.getsockname())
