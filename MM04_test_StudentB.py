
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
    (7.5),
    (9.25)
])
def test_impl2loz_GRADE20(module, solutions, value):
    expected = solutions.impl2loz(value)
    result = module.impl2loz(value)

    assert result == expected


def test_impl2loz_return_type_GRADE10(module):
    l, o = module.impl2loz(13.4)
    assert isinstance(l, int)
    assert isinstance(o, float)


@pytest.mark.parametrize("value", [
    (1128),
    (3443),
    (3351),
    (3333),
    (4331),
    (3423),
    (4533)
])
def test_pale(module, solutions, value):
    expected = solutions.pale(value)
    result = module.pale(value)

    assert result is expected


@pytest.mark.parametrize("author,title,city,publisher,year", [
    ("George R. R. Martin", "A Game of Thrones", "New York City", "Bantam Spectra", 1996),  # noqa: E501
    ("Jared Diamond", "Guns, Germs, and Steel: The Fates of Human Societies", "New York City", "W. W. Norton", 1997),  # noqa: E501
])
def test_bibformat(module, solutions, author, title, city, publisher, year):
    expected = solutions.bibformat(author, title, city, publisher, year)
    result = module.bibformat(author, title, city, publisher, year)

    assert result == expected


@pytest.mark.parametrize("author,title,city,publisher,year", [
    ("George R. R. Martin", "A Game of Thrones", "New York City", "Bantam Spectra", "1996"),  # noqa: E501
    ("Jared Diamond", "Guns, Germs, and Steel: The Fates of Human Societies", "New York City", "W. W. Norton", "1997"),  # noqa: E501
])
def test_bibformat_display(module, solutions, mock_input, mock_print, author, title, city, publisher, year):  # noqa: E501
    mock_input.side_effect = [title, author, year, publisher, city]

    with mock.patch.object(module, "bibformat") as mock_bibformat:
        mock_bibformat.return_value = solutions.bibformat(author, title, city, publisher, int(year))  # noqa: E501
        module.bibformat_display()
        mock_bibformat.assert_called_with(author, title, city, publisher, int(year))  # noqa: E501
        mock_print.assert_called_with(mock_bibformat.return_value)


@pytest.mark.parametrize("x,y,z", [
    (80, 40, 31),
    (80, 41, 31),
    (8, 1, 31),
    (80, 1, 31),
    (80, 1001, -44),
    (-2, 1001, -43)
])
def test_compound(module, solutions, x, y, z):
    expected = solutions.compound(x, y, z)
    result = module.compound(x, y, z)

    assert result is expected


@pytest.mark.parametrize("value", [
    (11),
    (12),
    (10300),
    (1000000000)
])
def test_funct(module, solutions, value, mock_print):
    mock_print.reset_mock()
    solutions.funct(value)
    expected = mock_print.call_args.args[0]
    mock_print.reset_mock()
    module.funct(value)
    mock_print.assert_called_with(expected)


@pytest.mark.parametrize("value", [
    (5.4),
    (4),
    (1000),
    (4200231)
])
def test_gol(module, solutions, value):
    expected = solutions.gol(value)
    result = module.gol(value)

    assert result == expected
