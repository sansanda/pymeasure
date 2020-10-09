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
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range, strict_discrete_set

from pymeasure.instruments.keithley.buffer import KeithleyBuffer

import numpy as np
import time
from io import BytesIO
import re


def clist_validator(value, values): #ok
    """ Provides a validator function that returns a valid clist string
    for channel commands of the Keithley DAQ6510. Otherwise it raises a
    ValueError.

    :param value: A value to test
    :param values: A range of values (range, list, etc.)
    :raises: ValueError if the value is out of the range
    """
    # Convert value to list of strings
    if isinstance(value, str):
        clist = [value.strip(" @(),")]
    elif isinstance(value, (int, float)):
        clist = ["{:d}".format(value)]
    elif isinstance(value, (list, tuple, np.ndarray, range)):
        clist = ["{:d}".format(x) for x in value]
    else:
        raise ValueError("Type of value ({}) not valid".format(type(value)))

    # Pad numbers to length (if required)
    clist = [c.rjust(2, "0") for c in clist]
    clist = [c.rjust(3, "1") for c in clist]

    # print(clist)
    # print('values',values)
    # print(value)

    # Check channels against valid channels
    for c in clist:
        if int(c) not in values:
            raise ValueError("Channel number %s not valid." % c)

    # Convert list of strings to clist format
    clist = "(@{:s})".format(", ".join(clist))

    return clist


def text_length_validator(value, values):
    """ Provides a validator function that a valid string for the display
    commands of the Keithley. Raises a TypeError if value is not a string.
    If the string is too long, it is truncated to the correct length.

    :param value: A value to test
    :param values: The allowed length of the text
    """

    if not isinstance(value, str):
        raise TypeError("Value is not a string.")

    return value[:values]


class KeithleyDAQ6510(Instrument, KeithleyBuffer):
    """ Represents the Keithely DAQ6510 Multimeter/Switch System and provides a
    high-level interface for interacting with the instrument.

    .. code-block:: python

        keithley = KeithleyDAQ6510(Adapter)

    """

    # list of lists on every list has the description parameters of the cards installed in the instrument
    # p.e: [7700.0, '20Ch Mux w/CJC', '0.0.0a', 1324982.0] at CARDSLIST_VALUES[0] if a 7700 is plugged to the slot 1 of the daq6510
    # p.e: ['Empty Slot'] at CARDSLIST_VALUES[1] is none is plugged to the slot 2 of the daq6510
    CARDSLIST_VALUES = list()
    #list of lists on every list has the valid channels of the card installed in the instrument
    #p.e: [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122]
    # at CHANNELSLIST_VALUES[0] is a 7700 card is pugged to the slot 1 of the instrument
    CHANNELSLIST_VALUES = list()

    # Routing commands
    closed_channels = Instrument.control(
        "ROUTe:MULTiple:CLOSe?", "ROUTe:MULTiple:CLOSe %s",
        """ Parameter that controls the opened and closed channels.
        All mentioned channels are closed, other channels will be opened.
        """,
        validator=clist_validator,
        values=CHANNELSLIST_VALUES,
        check_get_errors=True,
        check_set_errors=True,
        separator=None,
        get_process=lambda v: [
            int(vv) for vv in (v.strip(" ()@,").split(",")) if not vv == ""
        ],
    )

    open_channels = Instrument.setting(
        "ROUTe:MULTiple:OPEN %s",
        """ A parameter that opens the specified list of channels. Can only
        be set.
        """,
        validator=clist_validator,
        values=CHANNELSLIST_VALUES,
        check_set_errors=True
    )

    def get_state_of_channels(self, channels):#ok
        """ Get the open or closed state of the specified channels

        :param channels: a list of channel numbers, or single channel number
        """
        clist = clist_validator(channels, self.CHANNELSLIST_VALUES)
        #print("ROUTe:MULTiple:STATe? %s" % clist + '\n')
        state = self.ask("ROUTe:STATe? %s" % clist + '\n')
        #print(state)
        return state

    def open_all_channels(self): #ok
        """ Open all channels of the Keithley DAQ6510.
        """
        self.write(":ROUTe:OPEN:ALL\n")

    def __init__(self, adapter, **kwargs):
        super(KeithleyDAQ6510, self).__init__(adapter, "Keithley DAQ 6510 MultiMeter/Switch System", **kwargs)
        self.reset()
        self.check_errors()
        self.determine_installed_cards()
        self.determine_valid_channels()
        #print(self.CHANNELSLIST_VALUES)
        self.open_rows_to_columns(1,(1,2,3,4))

    def determine_installed_cards(self):#ok

        self.CARDSLIST_VALUES.append(self.values("syst:card1:idn?\n", separator=","))
        self.CARDSLIST_VALUES.append(self.values("syst:card2:idn?\n", separator=","))

    def determine_valid_channels(self):#ok
        """ Determine what channels are valid from the installed cards. """

        self.CHANNELSLIST_VALUES.clear()
        for slotNumber, card in enumerate(self.CARDSLIST_VALUES,1):
            if str(card[0]) == 'Empty Slot':
                continue
            elif str(card[0]) == '7700.0':
                #print(card)
                """The 7700 is a 10(columns) x 2(rows) matrix card and two
                #   AC-DC Current(21 & 22) channels and three additional switches (23, 24, 25)   
                #   that allow row 1 and 2 to be connected to the DMM backplane (input and sense respectively).
                #   """
                channels = range(1, 23)
            else:
                log.warning("Card type %s at slot %s is not yet implemented." % (card, slotNumber))

            channels = [100 * slotNumber + ch for ch in channels]
            self.CHANNELSLIST_VALUES.extend(channels)

    def close_rows_to_columns(self, rows, columns, cardModel='7700', cardNRows=2, cardNColumns=10, slot=1):
        """ Closes (connects) the channels between column(s) and row(s)
        of the cardModel connection matrix.
        Only one of the parameters `rows' or 'columns' can be "all"

        :param rows: row number or list of numbers; can also be "all"
        :param columns: column number or list of numbers; can also be "all"
        :param slot: slot number (1 or 2) of the DAQ6510
        """

        channels = self.channels_from_rows_columns(rows, columns,cardModel, cardNRows, cardNColumns, slot)
        self.closed_channels = channels

    def open_rows_to_columns(self, rows, columns, cardModel='7700', cardNRows=2, cardNColumns=10, slot=1):
        """ Opens (disconnects) the channels between column(s) and row(s)
        of the cardModel connection matrix.
        Only one of the parameters `rows' or 'columns' can be "all"

        :param rows: row number or list of numbers; can also be "all"
        :param columns: column number or list of numbers; can also be "all"
        :param slot: slot number (1 or 2) of the DAQ6510
        """

        channels = self.channels_from_rows_columns(rows, columns,cardModel, cardNRows, cardNColumns, slot)
        self.open_channels = channels

    def channels_from_rows_columns(self, rows, columns, cardModel, cardNRows, cardNColumns, slot=None):
        """ Determine the channel numbers between column(s) and row(s) of the
        cardModel connection matrix. Returns a list of channel numbers.
        Only one of the parameters `rows' or 'columns' can be "all"

        :param rows: row number or list of numbers; can also be "all". Rows starts from 1
        :param columns: column number or list of numbers; can also be "all". Columns starts from 0
        :param slot: slot number (1 or 2) of the DAQ6510 card to be used

        In

        """


        if 1 > slot > 2:
            raise ValueError("Parameter slot must be 1 or 2") #DAQ6510 only have 2 slots

        if (slot is not None) and (self.CARDSLIST_VALUES[slot-1][0] != float(cardModel)):
            raise ValueError("No " + cardModel + " card installed in slot %g" % slot)

        if isinstance(rows, str) and isinstance(columns, str):
            raise ValueError("Only one parameter can be 'all'")
        elif isinstance(rows, str) and rows == "all":
            rows = list(range(1, cardNRows+1))
        elif isinstance(columns, str) and columns == "all":
            columns = list(range(1, cardNColumns+1))

        if isinstance(rows, (list, tuple, np.ndarray)) and \
                isinstance(columns, (list, tuple, np.ndarray)):

            if len(rows) != len(columns):
                raise ValueError("The length of the rows and columns do not match")

            # Flatten (were necessary) the arrays
            new_rows = []
            new_columns = []
            for row, column in zip(rows, columns):
                if isinstance(row, int) and isinstance(column, int):
                    new_rows.append(row)
                    new_columns.append(column)
                elif isinstance(row, (list, tuple, np.ndarray)) and isinstance(column, int):
                    new_columns.extend(len(row) * [column])
                    new_rows.extend(list(row))
                elif isinstance(column, (list, tuple, np.ndarray)) and isinstance(row, int):
                    new_columns.extend(list(column))
                    new_rows.extend(len(column) * [row])

            rows = new_rows
            columns = new_columns

        # Determine channel number from rows and columns number.
        rows = np.array(rows)
        columns = np.array(columns)
        #print(rows)
        #print(columns)

        channels = (rows - 1) * cardNColumns + columns

        if slot is not None:
            channels += 100 * slot

        print(channels)
        return channels

    # system, some taken from Keithley 2400
    def beep(self, frequency, duration):
        """ Sounds a system beep.

        :param frequency: A frequency in Hz between 65 Hz and 2 MHz
        :param duration: A time in seconds between 0 and 7.9 seconds
        """
        self.write(":SYST:BEEP %g, %g" % (frequency, duration))

    def triad(self, base_frequency, duration):
        """ Sounds a musical triad using the system beep.

        :param base_frequency: A frequency in Hz between 65 Hz and 1.3 MHz
        :param duration: A time in seconds between 0 and 7.9 seconds
        """
        self.beep(base_frequency, duration)
        time.sleep(duration)
        self.beep(base_frequency * 5.0 / 4.0, duration)
        time.sleep(duration)
        self.beep(base_frequency * 6.0 / 4.0, duration)

    @property
    def error(self):#ok
        """ Returns a tuple of an error code and message from a
        single error. """
        err = self.values(":system:error?\n",separator=",")
        if len(err) < 2:
            err = self.read()  # Try reading again
        code = err[0]
        message = err[1].replace('"', '')
        return (code, message)

    def check_errors(self):#ok
        """ Logs any system errors reported by the instrument.
        """
        code, message = self.error
        while code != 0:
            t = time.time()
            log.info("Keithley DAQ6510 reported error: %d, %s" % (code, message))
            #print(code, message)
            code, message = self.error
            if (time.time() - t) > 10:
                log.warning("Timed out for Keithley DAQ6510 error retrieval.")

    def reset(self):#ok
        """ Resets the instrument and clears the queue.  """
        # self.write("status:queue:clear;*RST;:stat:pres;:*CLS;")
        self.write("*RST;:stat:pres;:*CLS;")

    options = Instrument.measurement(
        "*OPT?\n",
        """Property that lists the installed cards in the Keithley DAQ6510.
        Returns a dict with the integer card numbers on the position.""",
        cast=False
    )

    ###########
    # DISPLAY #
    ###########

    text_enabled = Instrument.control(
        "DISP:TEXT:STAT?", "DISP:TEXT:STAT %d",
        """ A boolean property that controls whether a text message can be
        shown on the display of the Keithley DAQ6510.
        """,
        values={True: 1, False: 0},
        map_values=True,
    )
    display_text = Instrument.control(
        "DISP:TEXT:DATA?", "DISP:TEXT:DATA '%s'",
        """ A string property that controls the text shown on the display of
        the Keithley DAQ6510. Text can be up to 12 ASCII characters and must be
        enabled to show.
        """,
        validator=text_length_validator,
        values=12,
        cast=str,
        separator="NO_SEPARATOR",
        get_process=lambda v: v.strip("'\""),
    )

    def display_closed_channels(self):
        """ Show the presently closed channels on the display of the Keithley
        DAQ6510.
        """

        # Get the closed channels and make a string of the list
        channels = self.closed_channels
        channel_string = " ".join([
            str(channel % 100) for channel in channels
        ])

        # Prepend "Closed: " or "C: " to the string, depending on the length
        str_length = 12
        if len(channel_string) < str_length - 8:
            channel_string = "Closed: " + channel_string
        elif len(channel_string) < str_length - 3:
            channel_string = "C: " + channel_string

        # enable displaying text-messages
        self.text_enabled = True

        # write the string to the display
        self.display_text = channel_string
