from unittest import mock
import sys
import os


def check_called(func):
    return mock.Mock(side_effect=func)


def disable_print():
    sys.stdout = open(os.devnull, 'w')


def enable_print():
    sys.stdout = sys.__stdout__


def print_message_in_characters(message, character, total_characters=50):
    NUM_DELIMITERS_ON_EACH_SIDE = int((total_characters - len(message))/2)
    print((character * NUM_DELIMITERS_ON_EACH_SIDE) + message + (character * NUM_DELIMITERS_ON_EACH_SIDE))


def verify_testcases_sheet(testcases_sheet, sheet_name):
    """
    Verify test cases excel sheet for valid column headers and data within cells.

    Parameters
    ----------
    testcases_sheet: testcases excel sheet to be verified
    sheet_name: name of sheet being verified

    Returns
    -------
    True if all tests are passed.
    """
    print("Verifying test case worksheet '" + sheet_name + "' is set up properly...",
          flush=True)  # Flush prevents errors printing first

    testcases_columns = testcases_sheet.columns

    REQ_COLUMNS = ["Command", "Student"]
    OPTIONAL_COLUMNS = ["DontTest", "Weight", "Outputs"]

    if "DontTest" in testcases_columns:
        # Make sure 'test' rows have appropriate data in columns
        test_rows = testcases_sheet[testcases_sheet["DontTest"].isnull()]
        if test_rows["Weight"].isna().any():
            raise SyntaxError("Missing items in \"Weight\" column")

    for col in REQ_COLUMNS:
        if col not in testcases_columns:
            raise SyntaxError("Missing required column \"" + col + "\" in test case worksheet.")

        if True in list(testcases_sheet[col].isna()):
            raise SyntaxError("Column \"" + col + "\" is missing some entries.")

    for col in testcases_columns:
        if col not in REQ_COLUMNS and col not in OPTIONAL_COLUMNS:
            raise SyntaxError("Unknown column \"" + str(col) + "\" found in test case worksheet.")

    # TODO: If outputs are (the only thing) missing from the required columns, attempt to run testcaseUpdater

    print("Test case worksheet is properly set up.")
    return True
