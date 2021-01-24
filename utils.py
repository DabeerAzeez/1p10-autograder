from unittest import mock
import sys
import os

INSTRUCTIONS_SHEET_NAME = "Instructions"  # Name of Instructions sheet within test case excel file
# TODO: Use Python warning module


def check_called(func):
    """
    Creates a unittest Mock object which allows for checking whether a given function has been called.

    Usage: Use the @check_called decorator on a function of interest. From then on, the func.check_called attribute
           will denote whether the function has been called or not.

    Parameters
    ----------
    func: Function to check

    Returns
    -------
    Boolean indicating whether the function has been called or not
    """
    return mock.Mock(side_effect=func)


def disable_print():
    """Disable printing to the console"""
    sys.stdout = open(os.devnull, 'w')


def enable_print():
    """Enable printing to the console"""
    sys.stdout = sys.__stdout__


def print_message_in_characters(message, characters, total_characters=50):
    """
    Print a message in the middle of a list of repeating characters such that the total string is approximately a
    fixed length (some rounding errors occur to keep the string somewhat symmetrical).

    Parameters
    ----------
    message: message to be printed within the list of repeating characters
    characters: characters to repeat around the message when printed
    total_characters: total length of printed statement
    """
    NUM_DELIMITERS_ON_EACH_SIDE = int((total_characters - len(message))/(2*len(characters)))
    print((characters * NUM_DELIMITERS_ON_EACH_SIDE) + message + (characters * NUM_DELIMITERS_ON_EACH_SIDE))
