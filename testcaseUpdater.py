"""
1P10 Autograder Test Case Updater
Author: Dabeer Abdul-Azeez <abdulazd@mcmaster.ca>

This script automatically determines the appropriate outputs for test cases which are listed in the
"test case workbook" (hereafter TCWB) and then populates the TCWB appropriately. The completed TCWB can then be used by
the autograder script as an answer key.

Requirements to run this script:
- TCWB containing individual sheets for each computing lab which requires test cases
    - Check TCWB for instructions on how to write test cases
    - "Input cells" refer to all cells which require input in order for this script to run (i.e. function name,
       test case weight, inputs)
- Solution Python scripts (and any helper scripts for those) which house the functions referenced in the TCWB

This script will:
- Ask for a specific sheet of the TCWB (i.e. a specific milestone) whose test case outputs need updating
- Run through the appropriate sheet of the TCWB, passing the listed inputs through the listed functions and placing
the outputs in the appropriate column
- Sort all sheets in the TCWB alphabetically (to prevent sheets from going out of order when updating)

Notes:
- This version uses xlrd v1.2.0; newer versions do not support xlsx files
- Don't have any excel files open otherwise permission errors will occur when attempting to write to them
- Instructions on how to write test cases are included in the TCWB
"""

# TODO: Reset TCWB column widths
# TODO: Don't rely on old xlrd (https://stackoverflow.com/questions/65250207/pandas-cannot-open-an-excel-xlsx-file)
# TODO: Parameterize column names

import pandas as pd
import importlib
import openpyxl
import utils

TCWB_PATH = "TestCases/MiniMilestone_TestCases.xlsx"
SOLUTION_FILENAME_SUFFIX = "_SOLUTION"  # E.g. MM04_SOLUTION.py
INSTRUCTIONS_SHEET_NAME = "Instructions"  # Name of sheet within TEST_CASE_FILENAME containing instructions
# TODO: Modularize instructions sheet names to include other excluded sheets


def import_solution(module_name, level):
    """
    Imports given module's methods into selected namespace. Adapted from
    https://stackoverflow.com/questions/43059267/how-to-do-from-module-import-using-importlib

    Parameters
    ----------
    module_name: name of module to be imported
    level: Namespace level, whether "global" or "local"
    """
    if level not in ["global", "local"]:
        raise TypeError("Improper level chosen for importing solution module.")

    # get a handle on the module
    mdl = importlib.import_module(module_name)

    # is there an __all__?  if so respect it
    if "__all__" in mdl.__dict__:
        names = mdl.__dict__["__all__"]
    else:
        # otherwise we import all names that don't begin with _
        names = [x for x in mdl.__dict__ if not x.startswith("_")]

    # now drag them in
    if level == "global":
        globals().update({k: getattr(mdl, k) for k in names})
    elif level == "local":
        locals().update({k: getattr(mdl, k) for k in names})
    else:
        raise TypeError("Error updating selected namespace.")


def select_sheets(sheet_names_df):
    """
    Allows user to select a sheet from the TCWB for updating

    Parameters
    ----------
    sheet_names_df: Dataframe containing names of sheets in TCWB

    Returns
    -------
    List of selected sheet names
    """
    sheet_names_df = sheet_names_df[sheet_names_df['Sheet Name'] != INSTRUCTIONS_SHEET_NAME]  # Remove instruction sheet
    print(sheet_names_df, "\n")

    chosen_index = input("Please select the row number of the sheet you'd like to update. If you would like to "
                         "update ALL sheets, enter 'all': ").strip()

    if chosen_index == "all":
        return sheet_names_df.values.flatten()  # Return all sheet names; flattens numpy N-dimensional array

    try:
        chosen_index = int(chosen_index)
        if chosen_index not in sheet_names_df.index and chosen_index != -1:
            raise ValueError
    except ValueError:
        print("Please choose an appropriate option.\n")
        return select_sheets(sheet_names_df)

    return [sheet_names_df.loc[chosen_index].values[0]]


def verify_testcase_sheet(testcases_df, chosen_sheet):
    """
    Verify required columns are present in inputted columns

    Parameters
    ----------
    columns: Columns to be checked for required columns

    Returns
    -------
    String representing whether the function or object (or both) columns are present in 'columns'
    """

    # Check that required columns exist
    REQ_COLUMNS = ["Command", "Student", "Weight", "Outputs"]

    for col in REQ_COLUMNS:
        if col not in testcases_df.columns:
            raise SyntaxError("Missing " + col + " column or column header in sheet " + chosen_sheet)

    # Check that relevant columns are completely filled
    REQ_FULL_COLUMNS = ["Command", "Student", "Weight"]

    for col in REQ_FULL_COLUMNS:
        if testcases_df[col].isna().any():
            raise SyntaxError("Missing at least one entry in " + col + " column of sheet " + chosen_sheet)

    # Check columns for appropriate types of inputs
    try:
        # Check for non-alphabetic entries in the 'Student' column
        if testcases_df["Student"].apply(lambda x: not x.isalpha()).any():
            raise ValueError
    except (AttributeError, ValueError):
        raise ValueError("Non alphabetic character in Student column of sheet " + chosen_sheet)

    try:
        # Check for non-numeric entries in the 'Weight' column
        if testcases_df["Weight"].apply(lambda x: not isinstance(x, (int, float))).any():
            raise ValueError
    except (AttributeError, ValueError):
        raise ValueError("Non-numeric character in Weight column of sheet " + chosen_sheet)

    try:
        # Check for numeric entries in the 'Command' column
        if testcases_df["Command"].apply(lambda x: isinstance(x, (int, float))).any():
            raise ValueError
    except (AttributeError, ValueError):
        raise ValueError("Numeric character (not a command!) in Command column of sheet " + chosen_sheet)


def perform_tests(test_cases_df, chosen_sheet):
    """
    Auto-fills 'Outputs' column of selected sheet in test cases workbook by passing the inputs through
    the appropriate functions from the appropriates Python solution file.

    Parameters
    ----------
    test_cases_df: Pandas ExcelFile object of TCWB
    chosen_sheet: Chosen sheet of test cases workbook
    """

    # Import appropriate solution module
    try:
        import_solution("TestCases." + chosen_sheet + SOLUTION_FILENAME_SUFFIX, "global")  # TODO: test local version
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(str(e) + " --> missing solution module for selected test case excel sheet")

    # Run test for each row
    for index, row in test_cases_df.iterrows():  # iterrows generator should not be used for large dataframes
        test_code = "raise LookupError"

        try:
            if row["DontTest"] == "x":
                test_code = row['Command']  # Run the command, but don't treat it like a test (don't record output)
        except KeyError:
            test_code = "row['Outputs'] = str(" + row['Command'] + ")"

        try:
            exec(test_code)
        except LookupError:
            raise LookupError("Error retrieving test code from test case worksheet")
        except Exception as e:
            row_num = index + 2  # Account for header row and zero-based array indexing
            raise Exception(str(e) + " --> exception occurred in sheet " + chosen_sheet +
                            " row " + str(row_num) + " of test cases excel file.")

        test_cases_df.loc[index] = row  # Update test_cases dataframe with local row Series

    writer = pd.ExcelWriter(TCWB_PATH, engine='openpyxl', mode='a')

    book = openpyxl.load_workbook(TCWB_PATH)
    book.remove(book[chosen_sheet])  # Remove original sheet to prevent duplicates
    writer.book = book

    test_cases_df.to_excel(writer, chosen_sheet, index=False)  # Write updated test case sheet to excel file

    try:
        writer.save()
    except PermissionError:
        raise PermissionError("Access denied when writing to excel file; try closing all excel files and restarting.")

    writer.close()

    # Sort worksheets alphabetically
    # TODO: Sort sheets alphabetically without accessing a protected member
    # noinspection PyProtectedMember
    book._sheets.sort(key=lambda ws: ws.title)
    book.save(TCWB_PATH)


def main():
    test_case_xl = pd.ExcelFile(TCWB_PATH)
    sheet_names_df = pd.DataFrame(test_case_xl.sheet_names, columns=['Sheet Name'])

    print("Welcome to the testcaseUpdater. Below are the extracted sheets from the test case spreadsheet.\n")

    if INSTRUCTIONS_SHEET_NAME not in sheet_names_df.values:
        print(">>>> Warning: Missing instructions sheet in test case excel file <<<<<< \n")

    chosen_sheet_names = select_sheets(sheet_names_df)

    utils.disable_print()

    for chosen_sheet_name in chosen_sheet_names:
        test_cases_df = pd.read_excel(test_case_xl, sheet_name=chosen_sheet_name)  # Read chosen sheet
        verify_testcase_sheet(test_cases_df, chosen_sheet_name)
        perform_tests(test_cases_df, chosen_sheet_name)

    utils.enable_print()

    print("*" * 75)
    print(f"Update complete. Check {TCWB_PATH}. Press enter to quit.")
    input()


main()
