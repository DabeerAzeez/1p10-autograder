
import pytest
import unittest.mock as mock


# BOILER PLATE -- NEEDED BY THE TEST HARNESS
def assignment_module():
    pass


def solutions_module():
    pass


@pytest.fixture
def module():
    return assignment_module()


@pytest.fixture
def solutions():
    return solutions_module()
# END BOILER PLATE CODE


# Mocking print and input as fixtures since they're used often
@pytest.fixture
def mock_print():
    with mock.patch("builtins.print") as mock_print:
        yield mock_print


@pytest.fixture
def mock_input():
    with mock.patch("builtins.input") as mock_input:
        yield mock_input


#  INSERT PYTEST TESTS BELOW
@pytest.mark.parametrize("value", [
    (100),
    (32),
    (97),
    (50)
])
def test_f_to_k_GRADE20(module, solutions, value):
    expected = solutions.f_to_k(value)
    answer = module.f_to_k(value)
    assert answer == expected


def test_f_to_k_return_type_GRADE10(module):
    answer = module.f_to_k(100)

    assert isinstance(answer, float)


@pytest.mark.parametrize("name,city", [
    ("Natalia", "Belo Horizonte"),
    ("Jon Snow", "Winterfell")
])
def test_poem_generator_GRADE20(module, mock_input, mock_print, name, city):
    mock_input.side_effect = [name, city]
    module.poem_generator()

    poem_output = ""
    for call in mock_print.call_args_list:
        poem_output += call.args[0]
        poem_output += "\n"

    assert name in poem_output
    assert city in poem_output


def test_poem_generator_return_type_GRADE10(module, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '')
    assert module.poem_generator() is None