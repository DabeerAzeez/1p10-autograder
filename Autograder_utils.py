from unittest import mock


def check_called(func):
    return mock.Mock(side_effect=func)

