from unittest import mock
import sys
import os

INSTRUCTIONS_SHEET_NAME = "Instructions"  # Name of Instructions sheet within test case excel file


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


def verify_testcase_sheet(testcases_df, chosen_sheet_name):
    """
    Verify that a Dataframe representing the test cases Excel sheet has data in the appropriate cells.

    Parameters
    ----------
    testcases_df: Dataframe to be tested
    chosen_sheet_name: name of chosen sheet

    Returns
    -------
    True if all tests pass
    """
    print("Verifying test case worksheet '" + chosen_sheet_name + "' is set up properly...",
          flush=True)  # Flush prevents errors printing first

    # Check that required columns exist
    REQ_COLUMNS = ["Command", "Student", "Weight", "Outputs"]
    OPTIONAL_COLUMNS = ["DontTest"]

    for col in REQ_COLUMNS:
        if col not in testcases_df.columns:
            raise SyntaxError("Missing " + col + " column or column header in sheet " + chosen_sheet_name)

    # Check that relevant columns are completely filled
    REQ_FULL_COLUMNS = ["Command", "Student"]

    for col in REQ_FULL_COLUMNS:
        if testcases_df[col].isna().any():
            raise SyntaxError("Missing at least one entry in " + col + " column of sheet " + chosen_sheet_name)

    # Check columns for appropriate types of inputs
    try:
        # Check for non-alphabetic entries in the 'Student' column
        if testcases_df["Student"].apply(lambda x: not x.isalpha()).any():
            raise ValueError
    except (AttributeError, ValueError):
        raise ValueError("Non alphabetic character in Student column of sheet " + chosen_sheet_name)

    try:
        # Check for non-numeric entries in the 'Weight' column
        if testcases_df["Weight"].apply(lambda x: not isinstance(x, (int, float))).any():
            raise ValueError
    except (AttributeError, ValueError):
        raise ValueError("Non-numeric character in Weight column of sheet " + chosen_sheet_name)

    try:
        # Check for numeric entries in the 'Command' column
        if testcases_df["Command"].apply(lambda x: isinstance(x, (int, float))).any():
            raise ValueError
    except (AttributeError, ValueError):
        raise ValueError("Numeric character (not a command!) in Command column of sheet " + chosen_sheet_name)

    for col in testcases_df.columns:
        if col not in REQ_COLUMNS and col not in OPTIONAL_COLUMNS:
            raise ValueError("Unknown column \"" + str(col) + "\" found in test case worksheet.")

    if "DontTest" in testcases_df.columns:
        # Make sure 'test' rows have appropriate data in columns
        test_rows = testcases_df[testcases_df["DontTest"].isnull()]
        if test_rows["Weight"].isna().any():
            raise ValueError("Missing items in \"Weight\" column for rows to be tested for grades")

    print("Test case worksheet is properly set up.")
    return True


def verify_testcases_sheets(sheet_names_df):
    """
    Verify that a Dataframe representing the names of the sheets in the test cases Excel file is correctly set up.

    Parameters
    ----------
    sheet_names_df: Dataframe to be tested

    Returns
    -------
    True if all tests pass
    """
    if INSTRUCTIONS_SHEET_NAME not in sheet_names_df.values:
        print(">>>> Warning: Missing instructions sheet in test case excel file <<<<<< \n")

    return True
