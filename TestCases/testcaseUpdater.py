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

import pandas as pd
import importlib
import openpyxl
import sys
import os

TEST_CASE_FILENAME = "MiniMilestone_TestCases.xlsx"
SOLN_FILENAME_SUFFIX = "_SOLUTION"  # E.g. MM04_SOLUTION.py
INSTRUCTIONS_SHEETNAME = "Instructions"  # Name of sheet within TEST_CASE_FILENAME containing instructions
DELIMITER = ";"


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
    sheet_names_df = sheet_names_df[sheet_names_df['Sheet Name'] != INSTRUCTIONS_SHEETNAME]  # Remove instructions sheet
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


def verify_columns(columns):
    """
    Verify required columns are present in inputted columns

    Parameters
    ----------
    columns: Columns to be checked for required columns

    Returns
    -------
    String representing whether the function or object (or both) columns are present in 'columns'
    """
    # TODO: Check for missing items in required columns

    REQ_COLUMNS = ["Command", "Student", "Weight", "Outputs"]

    for col in REQ_COLUMNS:
        if col not in columns:
            raise SyntaxError("Missing " + col + " column in test case worksheet")


def perform_tests(test_case_xl, chosen_sheet):
    """
    Auto-fills 'Outputs' column of selected sheet in test cases workbook by passing the inputs through
    the appropriate functions from the appropriates Python solution file.

    Parameters
    ----------
    test_case_xl: Pandas ExcelFile object of TCWB
    chosen_sheet: Chosen sheet of test cases workbook
    """
    test_cases_df = pd.read_excel(test_case_xl, sheet_name=chosen_sheet)  # Read chosen sheet
    import_solution(chosen_sheet + SOLN_FILENAME_SUFFIX, "global")  # Import appropriate solution module # TODO: test local version

    verify_columns(test_cases_df.columns)

    # Run test for each row
    for index, row in test_cases_df.iterrows():  # iterrows generator should not be used for large dataframes
        test_code = ""

        if "DontTest" in list(row.index):
            if row["DontTest"] == "x":
                test_code = row['Command']  # Run the command, but don't treat it like a test (don't record output)
            else:
                test_code = "row['Outputs'] = str(" + row['Command'] + ")"

        exec(test_code)
        test_cases_df.loc[index] = row  # Update test_cases dataframe with local row Series

    writer = pd.ExcelWriter(TEST_CASE_FILENAME, engine='openpyxl', mode='a')

    book = openpyxl.load_workbook(TEST_CASE_FILENAME)
    book.remove(book[chosen_sheet])  # Remove original sheet to prevent duplicates
    writer.book = book

    test_cases_df.to_excel(writer, chosen_sheet, index=False)  # Write updated test case sheet to excel file

    try:
        writer.save()
    except PermissionError:
        raise PermissionError("Access denied when writing to excel file; try closing all excel files and restarting.")

    writer.close()

    # Sort worksheets alphabetically
    book._sheets.sort(key=lambda ws: ws.title)
    book.save(TEST_CASE_FILENAME)


def main():
    test_case_xl = pd.ExcelFile(TEST_CASE_FILENAME)
    sheet_names_df = pd.DataFrame(test_case_xl.sheet_names, columns=['Sheet Name'])

    print("Welcome to the testcaseUpdater. Below are the extracted sheets from the test case spreadsheet.\n")

    chosen_sheet_names = select_sheets(sheet_names_df)

    sys.stdout = open(os.devnull, 'w')  # Disable print

    for sheet_name in chosen_sheet_names:
        perform_tests(test_case_xl, sheet_name)

    sys.stdout = sys.__stdout__  # Enable print

    print("*" * 75)
    print(f"Update complete. Check {TEST_CASE_FILENAME}. Press enter to quit.")
    input()


main()
