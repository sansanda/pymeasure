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

from decimal import Decimal
import numpy as np


def clist_validator(value, values):  # ok
    """ Provides a validator function that returns a valid clist string
    for channel commands of the Keithley DAQ6510. Otherwise it raises a
    ValueError.

    :param value: A value to test
    :param values: A range of values (range, list, etc.)
    :raises: ValueError if the value is out of the range

    For example
    """
    # Convert value to list of strings
    if isinstance(value, str):
        clist = [value.strip(" @(),")]
    elif isinstance(value, (int, float, np.int32)):
        clist = ["{:d}".format(value)]
    elif isinstance(value, (list, tuple, np.ndarray, range)):
        clist = ["{:d}".format(x) for x in value]
    else:
        raise ValueError("Type of value ({}) not valid".format(type(value)))

    # Pad numbers to length (if required)
    clist = [c.rjust(2, "0") for c in clist]
    clist = [c.rjust(3, "1") for c in clist]

    #print(clist)
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

def strict_range(value, values):
    """ Provides a validator function that returns the value
    if its value is less than the maximum and greater than the
    minimum of the range. Otherwise it raises a ValueError.

    :param value: A value to test
    :param values: A range of values (range, list, etc.)
    :raises: ValueError if the value is out of the range
    """
    if min(values) <= value <= max(values):
        return value
    else:
        raise ValueError('Value of {:g} is not in range [{:g},{:g}]'.format(
            value, min(values), max(values)
        ))


def strict_discrete_range(value, values, step):
    """ Provides a validator function that returns the value
    if its value is less than the maximum and greater than the
    minimum of the range and is a multiple of step.
    Otherwise it raises a ValueError.

    :param value: A value to test
    :param values: A range of values (range, list, etc.)
    :param step: Minimum stepsize (resolution limit)
    :raises: ValueError if the value is out of the range
    """
    # use Decimal type to provide correct decimal compatible floating
    # point arithmetic compared to binary floating point arithmetic
    if (strict_range(value, values) == value and
            Decimal(str(value)) % Decimal(str(step)) == 0):
        return value
    else:
        raise ValueError('Value of {:g} is not a multiple of {:g}'.format(
            value, step
        ))


def strict_discrete_set(value, values):
    """ Provides a validator function that returns the value
    if it is in the discrete set. Otherwise it raises a ValueError.

    :param value: A value to test
    :param values: A set of values that are valid
    :raises: ValueError if the value is not in the set
    """
    if value in values:
        return value
    else:
        raise ValueError('Value of {} is not in the discrete set {}'.format(
            value, values
        ))

def truncated_range(value, values):
    """ Provides a validator function that returns the value
    if it is in the range. Otherwise it returns the closest
    range bound.

    :param value: A value to test
    :param values: A set of values that are valid
    """
    if min(values) <= value <= max(values):
        return value
    elif value > max(values):
        return max(values)
    else:
        return min(values)


def modular_range(value, values):
    """ Provides a validator function that returns the value
    if it is in the range. Otherwise it returns the value,
    modulo the max of the range.

    :param value: a value to test
    :param values: A set of values that are valid
    """
    return value % max(values)


def modular_range_bidirectional(value, values):
    """ Provides a validator function that returns the value
    if it is in the range. Otherwise it returns the value,
    modulo the max of the range. Allows negative values.

    :param value: a value to test
    :param values: A set of values that are valid
    """
    if value > 0:
        return value % max(values)
    else:
        return -1 * (abs(value) % max(values))


def truncated_discrete_set(value, values):
    """ Provides a validator function that returns the value
    if it is in the discrete set. Otherwise, it returns the smallest
    value that is larger than the value.

    :param value: A value to test
    :param values: A set of values that are valid
    """
    # Force the values to be sorted
    values = list(values)
    values.sort()
    for v in values:
        if value <= v:
            return v

    return values[-1]


def discreteTruncate(number, discreteSet):
    """ Truncates the number to the closest element in the positive discrete set.
    Returns False if the number is larger than the maximum value or negative.
    """
    if number < 0:
        return False
    discreteSet.sort()
    for item in discreteSet:
        if number <= item:
            return item
    return False

def joined_validators(*validators):
    """ Join a list of validators together as a single.
    Expects a list of validator functions and values.

    :param validators: an iterable of other validators
    """

    def validate(value, values):
        for validator, vals in zip(validators, values):
            try:
                return validator(value, vals)
            except (ValueError, TypeError):
                pass
        raise ValueError("Value of {} not in chained validator set".format(value))

    return validate

def joined_validators_values(*validators_list, separator=","):
    """ Join a list of validators together as a single.
    But, we will validate each value_to_validate with it corresponent valid_values list.
    As a consequence validators list, values_to_validate list and valid_values list must to have the same size.
    Expects a three lists: validator functions list, values_to_validate list and valid_values list.

    :param validators: an iterable of other validators
    """

    def validate(values_to_validate_list, valid_values_list):
        result = ''
        for validator, values_to_validate, valid_values in zip(validators_list, values_to_validate_list, valid_values_list):
            try:
                result = result + str(validator(values_to_validate, valid_values)) + separator
            except ValueError as e:
                print(str(e))
                pass
        return result[:-1]
    return validate

def test_validators():
    modes = {
        'current': 'CURR:DC',
        'current ac': 'CURR:AC',
        'voltage': 'VOLT:DC',
        'voltage ac': 'VOLT:AC',
        'resistance': 'RES',
        'resistance 4W': 'FRES',
        'diode': 'DIOD',
        'capacitance': 'CAP',
        'temperature': 'TEMP',
        'continuity': 'CONT',
        'frequency': 'FREQ',
        'period': 'PER',
        'voltage dc ratio': 'VOLT:DC:RATIO',
        'digitize voltage': 'DIG:VOLT',
        'digitize current': 'DIG:CURR'
    }

    jvv = joined_validators_values(strict_discrete_set, clist_validator)


    values_to_validate_list = (modes.get('voltage'),[101,102,103])
    valid_values_list = [
        modes.values(), [101,102,103,104,105,106,107,108,109]

    ]
    print(jvv(values_to_validate_list, valid_values_list))

    jvv2 = joined_validators_values(strict_range, clist_validator)
    values_to_validate_list = (1, [101, 102, 103])
    valid_values_list = [
        [0.0005,12], [101, 102, 103, 104, 105, 106, 107, 108, 109]

    ]
    print(jvv2(values_to_validate_list, valid_values_list))

#test_validators()
