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
import numpy as np
import time
from io import BytesIO
import re

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument
from pymeasure.instruments.keithley.buffer import KeithleyBuffer

from pymeasure.instruments.validators import text_length_validator, strict_range
from pymeasure.instruments.validators import clist_validator
from pymeasure.instruments.validators import truncated_range, strict_discrete_set
from pymeasure.instruments.validators import joined_validators_values


class KeithleyDAQ6510(Instrument, KeithleyBuffer):

    """ Represents the Keithely DAQ6510 Multimeter/Switch System and provides a
    high-level interface for interacting with the instrument.

    .. code-block:: python

        keithley = KeithleyDAQ6510(Adapter)

    """

    FUNCTIONS = {
        'current': "'CURR:DC'",
        'current ac': "'CURR:AC'",
        'voltage': "'VOLT:DC'",
        'voltage ac': "'VOLT:AC'",
        'resistance': "'RES'",
        'resistance 4W': "'FRES'",
        'diode': "'DIOD'",
        'capacitance': "'CAP'",
        'temperature': "'TEMP'",
        'continuity': "'CONT'",
        'frequency': "'FREQ'",
        'period': "'PER'",
        'voltage dc ratio': "'VOLT:DC:RATIO'",
        'digitize voltage': "'DIG:VOLT'",
        'digitize current': "'DIG:CURR'"
    }

    # list of lists on every list has the description parameters of the cards installed in the instrument
    # p.e: [7700.0, '20Ch Mux w/CJC', '0.0.0a', 1324982.0] at CARDSLIST_VALUES[0] if a 7700 is plugged to the slot 1 of the daq6510
    # p.e: ['Empty Slot'] at CARDSLIST_VALUES[1] is none is plugged to the slot 2 of the daq6510
    CARDSLIST_VALUES = list()
    # list of lists on every list has the valid channels of the card installed in the instrument
    # p.e: [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122]
    # at CHANNELSLIST_VALUES[0] is a 7700 card is pugged to the slot 1 of the instrument
    CHANNELSLIST_VALUES = list()

    # Routing commands
    closed_channels = Instrument.control(
        "ROUTe:MULTiple:CLOSe?\n", "ROUTe:MULTiple:CLOSe %s\n",
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
        "ROUTe:MULTiple:OPEN %s\n",
        """ A parameter that opens the specified list of channels. Can only
        be set.
        """,
        validator=clist_validator,
        values=CHANNELSLIST_VALUES,
        check_set_errors=True
    )


    mode = Instrument.control(
        ":SENS:FUNC?\n", "SENS:FUNC %s\n",
        """ A string property that controls the configuration mode for measurements,
        which can take the values: 
        :code:'current' (DC), 
        :code:'current ac',
        :code:'voltage' (DC),  
        :code:'voltage ac', 
        :code:'resistance' (2-wire),
        :code:'resistance 4W' (4-wire), 
        :code:'period', 
        :code:'frequency',
        :code:'temperature', 
        :code:'diode', 
        :code:'capacitance',
        :code:'voltage dc ratio',
        :code:'digitize voltage',
        :code:'digitize current' and
        :code:'continutity' """,
        validator=joined_validators_values(strict_discrete_set,clist_validator, separator=","),
        values=(FUNCTIONS.values(), CHANNELSLIST_VALUES),
        map_values=False,
        get_process=lambda v: v.replace('"', '')
    )



    ###############
    # Voltage (V) #
    ###############

    voltage = Instrument.measurement(":READ?\n",
                                     """ Reads the voltage in Volts, if configured for this reading.
                                     """
                                     )

    voltage_range = Instrument.control(
        ":SENS:VOLT:RANG?\n", ":SENS:VOLT:RANG:AUTO 0;:SENS:VOLT:RANG %g\n",
        """ A floating point property that controls the measurement voltage
        range in Volts, which can take values from 100mV to 1000 V.
        Auto-range is disabled when this property is set. """,
        validator=truncated_range,
        values=[0.1, 1000]
    )

    voltage_ac_range = Instrument.control(
        ":SENS:VOLT:AC:RANG?\n", ":SENS:VOLT:RANG:AUTO 0;:SENS:VOLT:AC:RANG %g\n",
        """ A floating point property that controls the AC voltage range in
        Volts, which can take values from 100mV to 750 V.
        Auto-range is disabled when this property is set. """,
        validator=truncated_range,
        values=[0.1, 750]
    )

    # voltage_nplc = Instrument.control(
    #     ":SENS:VOLT:NPLC?\n", ":SENS:VOLT:NPLC %g\n",
    #     """ A floating point property that controls the number of power line cycles
    #     (NPLC) for the DC voltage measurements, which sets the integration period
    #     and measurement speed. Takes values from 0.01 to 10, where 0.1, 1, and 10 are
    #     Fast, Medium, and Slow respectively. """
    # )

    voltage_nplc = Instrument.control(
        ":SENS:VOLT:NPLC?\n", ":SENS:VOLT:NPLC %s\n",
        """ A string property that controls the configuration nplc for measurements,
        which can take the values: 0.0005 to 15 (60 Hz) or 12 (50 Hz or 400 Hz) """,
        validator=joined_validators_values(strict_range,clist_validator,separator=','),
        values=([0.0005,12], CHANNELSLIST_VALUES),
        map_values=False,
        get_process=lambda v: v.replace('"', '')
    )



    def get_state_of_channels(self, channels):  # ok
        """ Get the open or closed state of the specified channels

        :param channels: a list of channel numbers, or single channel number
        """
        clist = clist_validator(channels, self.CHANNELSLIST_VALUES)
        #print("ROUTe:MULTiple:STATe? %s" % clist + '\n')
        state = self.ask("ROUTe:STATe? %s" % clist + '\n')
        # print(state)
        return state

    def open_all_channels(self):  # ok
        """ Open all channels of the Keithley DAQ6510.
        """
        self.write(":ROUTe:OPEN:ALL\n")

    def __init__(self, adapter, **kwargs):
        super(KeithleyDAQ6510, self).__init__(adapter, "Keithley DAQ 6510 MultiMeter/Switch System", **kwargs)
        self.reset()
        self.check_errors()
        self.determine_installed_cards()
        self.determine_valid_channels()

    def determine_installed_cards(self):  # ok

        """ Determine what cards are intalled from the DAQ6510. """
        self.CARDSLIST_VALUES.append(self.values("syst:card1:idn?\n", separator=","))
        self.CARDSLIST_VALUES.append(self.values("syst:card2:idn?\n", separator=","))

    def determine_valid_channels(self):  # ok

        """ Determine what channels are valid from the installed cards. """
        self.CHANNELSLIST_VALUES.clear()
        for slotNumber, card in enumerate(self.CARDSLIST_VALUES, 1):
            if str(card[0]) == 'Empty Slot':
                continue
            elif str(card[0]) == '7700.0':
                # print(card)
                """The 7700 is a 10(columns) x 2(rows) matrix card and two
                #   AC-DC Current(21 & 22) channels and three additional switches (23, 24, 25)   
                #   that allow row 1 and 2 to be connected to the DMM backplane (input and sense respectively).
                #   """
                channels = range(1, 23)
            else:
                log.warning("Card type %s at slot %s is not yet implemented." % (card, slotNumber))

            channels = [100 * slotNumber + ch for ch in channels]
            self.CHANNELSLIST_VALUES.extend(channels)

    def close_individual_channels(self, channels):
        """ Closes (connects) the channels of the cardModel connection matrix.

        :param channels: list or tuple of channels to close; can also be "all"
            """
        if isinstance(channels, str) and channels == "all":
            self.closed_channels = self.CHANNELSLIST_VALUES
        else: self.closed_channels = channels

    def open_individual_channels(self, channels):
        """ Opens (unconnects) the channels of the cardModel connection matrix.

        :param channels: list or tuple of channels to open; can also be "all"
            """
        if isinstance(channels, str) and channels == "all":
            self.open_channels = self.CHANNELSLIST_VALUES
        else: self.open_channels = channels

    def close_rows_to_columns(self, rows, columns, cardModel='7700', cardNRows=2, cardNColumns=10, instrumentNSlots=2, slot=1):  # ok
        """ Closes (connects) the channels between column(s) and row(s)
        of the cardModel connection matrix.
        Only one of the parameters `rows' or 'columns' can be "all"
        For example: If we have installed at the slot 1 a 7700 card which has only 2 rows and ten columns per row
        and we want to close the channels 101, 102 and 103, then the parameters will be
        slot=1, rows = 1 and columns = (1,2,3)

        :param rows: row number or list of numbers only between 1 and 2 for cardModel='7700'; can also be "all"
        :param columns: column number or list of numbers only between 1 and 10 for cardModel='7700; can also be "all"
        :param cardModel: The model of the card installed in the DAQ6510
        :param cardNRows: The number of rows of the card installed int the DAQ6510
        :param cardNColumns: The number of columns of the card installed in the DAQ6510
        :param slot: slot number (1 or 2) of the DAQ6510
        """

        channels = self.channels_from_rows_columns(rows, columns, cardModel, cardNRows, cardNColumns, instrumentNSlots, slot)
        self.closed_channels = channels

    def open_rows_to_columns(self, rows, columns, cardModel='7700', cardNRows=2, cardNColumns=10, instrumentNSlots=2, slot=1):  # ok
        """ Opens (disconnects) the channels between column(s) and row(s)
        of the cardModel connection matrix.
        Only one of the parameters `rows' or 'columns' can be "all"
        For example: If we have installed at the slot 1 a 7700 card which has only 2 rows and ten columns per row
        and we want to open the channels 101, 102 and 103, then the parameters will be
        slot=1, rows = 1 and columns = (1,2,3)


        :param rows: row number or list of numbers only between 1 and 2 for cardModel='7700'; can also be "all"
        :param columns: column number or list of numbers only between 1 and 10 for cardModel='7700; can also be "all"
        :param cardModel: The model of the card installed in the DAQ6510
        :param cardNRows: The number of rows of the card installed int the DAQ6510
        :param cardNColumns: The number of columns of the card installed in the DAQ6510
        :param slot: slot number (1 or 2) of the DAQ6510
        """

        channels = self.channels_from_rows_columns(rows, columns, cardModel, cardNRows, cardNColumns, instrumentNSlots, slot)
        self.open_channels = channels

    def channels_from_rows_columns(self, rows, columns, cardModel, cardNRows, cardNColumns, instrumentNSlots, slot=None):#ok
        """ Determine the channel numbers between column(s) and row(s) of the
        cardModel connection matrix. Returns a list of channel numbers.
        Only one of the parameters `rows' or 'columns' can be "all"
        For example: If we have installed at the slot 1 a 7700 card which has only 2 rows and ten columns per row
        and we want to determine the channel numbers between column = (1,2,3) and row = 1 then the parameters will be
        slot=1, rows = 1 and columns = (1,2,3) and the result returned will be [101, 102, 103]

        :param rows: row number or list of numbers; can also be "all"
        :param columns: column number or list of numbers; can also be "all"
        :param cardModel: The model of the card installed in the DAQ6510
        :param cardNRows: The number of rows of the card installed int the DAQ6510
        :param cardNColumns: The number of columns of the card installed in the DAQ6510
        :param slot: slot number (1 or 2) of the DAQ6510

        """

        if slot not in range(1,instrumentNSlots+1):
            raise ValueError("Parameter slot must be between 1 and %s" % instrumentNSlots)  # 7700 only have 2 slots

        if isinstance(rows,int) and (not rows in range(1,cardNRows+1)):
            raise ValueError("Parameter rows must be between 1 and %s" % cardNRows)  # 7700 only have 2 rows

        if isinstance(rows, tuple) or isinstance(rows, list):
            if not set(rows).issubset([(i) for i  in range(1,cardNRows+1)]):
                raise ValueError("Parameter rows must be between 1 and %s" % cardNRows)  # 7700 only have 2 rows

        if isinstance(columns,int) and (not columns in range(1,cardNColumns+1)):
            raise ValueError("Parameter columns must be between 1 and %s" % cardNColumns)  # 7700 only have 10 columns

        if isinstance(columns, tuple) or isinstance(columns, list):
            if not set(columns).issubset([(i) for i  in range(1,cardNColumns+1)]):
                raise ValueError("Parameter columns must be between 1 and %s" % cardNColumns)  # 7700 only have 10 columns

        if (slot is not None) and (self.CARDSLIST_VALUES[slot - 1][0] != float(cardModel)):
            raise ValueError("No " + cardModel + " card installed in slot %g" % slot)


        if isinstance(rows, str) and isinstance(columns, str):
            raise ValueError("Only one parameter can be 'all'")
        elif isinstance(rows, str) and rows == "all":
            rows = list(range(1, cardNRows + 1))
        elif isinstance(columns, str) and columns == "all":
            columns = list(range(1, cardNColumns + 1))

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
        # print(rows)
        # print(columns)

        channels = (rows - 1) * cardNColumns + columns

        if slot is not None:
            channels += 100 * slot

        #print(channels)
        return channels

    # system, some taken from Keithley DAQ6510
    def beep(self, frequency, duration):#ok
        """ Sounds a system beep.

        :param frequency: A frequency in Hz between 65 Hz and 2 MHz
        :param duration: A time in seconds between 0 and 7.9 seconds
        """
        self.write(":SYST:BEEP %g, %g\n" % (frequency, duration))

    def triad(self, base_frequency, duration):#ok
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
    def error(self):  # ok
        """ Returns a tuple of an error code and message from a
        single error. """
        err = self.values(":system:error?\n", separator=",")
        if len(err) < 2:
            err = self.read()  # Try reading again
        code = err[0]
        message = err[1].replace('"', '')
        return (code, message)

    def check_errors(self):  # ok
        """ Logs any system errors reported by the instrument.
        """
        code, message = self.error
        while code != 0:
            t = time.time()
            log.info("Keithley DAQ6510 reported error: %d, %s" % (code, message))
            # print(code, message)
            code, message = self.error
            if (time.time() - t) > 10:
                log.warning("Timed out for Keithley DAQ6510 error retrieval.")

    def reset(self):  # ok
        """ Resets the instrument and clears the queue.  """
        # self.write("status:queue:clear;*RST;:stat:pres;:*CLS;")
        self.write("*RST;:stat:pres;:*CLS;\n")


    ###########
    # DISPLAY #
    ###########

    display_control = Instrument.control(
        "DISPlay:LIGHt:STATe?\n", "DISPlay:LIGHt:STATe %s\n",
        """A property that sets the light output level of the front-panel display of the Keithley DAQ6510.""",
        values={100: 'ON100', 75: 'ON75', 50: 'ON50', 25: 'ON25', 0: 'OFF', 'ALLOFF': 'BLACkout'},
        map_values=True,
    )

    display_text_at_topline = Instrument.setting(
        "DISPlay:USER1:TEXT:DATA '%s'\n",
        """ A string property that controls the text shown on the top line of the display of
        the Keithley DAQ6510. Text can be up to 12 ASCII characters and must be
        enabled to show.
        """,
        validator=text_length_validator,
        values=20,
        cast=str,
        separator="NO_SEPARATOR",
        get_process=lambda v: v.strip("'\""),
    )

    display_text_at_bottomline = Instrument.setting(
        "DISPlay:USER2:TEXT:DATA '%s'\n",
        """ A string property that controls the text shown on the bottom line of the  the display of
        the Keithley DAQ6510. Text can be up to 12 ASCII characters and must be
        enabled to show.
        """,
        validator=text_length_validator,
        values=32,
        cast=str,
        separator="NO_SEPARATOR",
        get_process=lambda v: v.strip("'\""),
    )

    def display_closed_channels(self, line=1, brightness=75):#ok
        """ Show the presently closed channels on the display of the Keithley DAQ6510.

        :param line: 1 for displaying at top line, 2 for displaying at bottom line or 0 for both

        """
        if line not in (0, 1, 2): return

        str_length_for_bottomline = 32
        str_length_for_topline = 20

        # control the display
        self.display_control = brightness

        # Get the closed channels and make a string of the list
        channels = self.closed_channels
        channel_string = " ".join([
            str(channel % 100) for channel in channels
        ])

        # Prepend "Closed: " or "C: " to the string, depending on the length

        if len(channel_string) < str_length_for_topline - 8:
            channel_string_for_topline = "Closed: " + channel_string
        else:
            channel_string_for_topline = "C: " + channel_string

        channel_string_for_topline = channel_string_for_topline[0:str_length_for_topline]

        if len(channel_string) < str_length_for_bottomline - 8:
            channel_string_for_bottomline = "Closed: " + channel_string
        else:
            channel_string_for_bottomline = "C: " + channel_string

        channel_string_for_bottomline = channel_string_for_bottomline[0:str_length_for_bottomline]

        # write the string to the display
        if line==1:
            self.display_text_at_topline = channel_string_for_topline
        elif line==2:
            self.display_text_at_bottomline = channel_string_for_bottomline
        else:
            self.display_text_at_topline = channel_string_for_topline
            self.display_text_at_bottomline = channel_string_for_bottomline

    def display_text(self, text, line=1, brightness=75):#ok
        """ Show a text on the display of the Keithley DAQ6510.

        :param line: 1 for displaying at top line, 2 for displaying at bottom line or 0 for both

        """
        if line not in (0, 1, 2) or (not isinstance(text,str)): return

        str_length_for_bottomline = 32
        str_length_for_topline = 20

        # control the display
        self.display_control = brightness

        # write the string to the display
        if line==1:
            self.display_text_at_topline = text[0:str_length_for_topline]
        elif line==2:
            self.display_text_at_bottomline = text[0:str_length_for_bottomline]
        else:
            self.display_text_at_topline = text[0:str_length_for_topline]
            self.display_text_at_bottomline = text[0:str_length_for_bottomline]

    def clear_display(self):#ok
        self.write(':DISPlay:CLEar\n')

    ###########
    # MEASURE #
    ###########

    def config_and_measure_voltage(self, channels, max_voltage=1, ac=False, nplc=1):
        """ Configures the instrument to measure voltage,
        based on a maximum voltage to set the range, and
        a boolean flag to determine if DC or AC is required.

        :param channels: an int, list or tuple containing the channels where measure the voltage
        :param max_voltage: A voltage in Volts to set the voltage range
        :param ac: False for DC voltage, and True for AC voltage
        """


        if ac:
            self.mode = 'voltage ac'
            #self.voltage_ac_range = max_voltage
        else:
            self.voltage_nplc = nplc, channels
            self.mode = self.FUNCTIONS.get('voltage'), channels

            #self.voltage_range = max_voltage


