from unittest import mock
import sys
import os


def check_called(func):
    return mock.Mock(side_effect=func)


def disable_print():
    sys.stdout = open(os.devnull, 'w')


def enable_print():
    sys.stdout = sys.__stdout__
