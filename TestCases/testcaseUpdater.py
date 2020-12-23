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

# TODO: Don't rely on old xlrd (https://stackoverflow.com/questions/65250207/pandas-cannot-open-an-excel-xlsx-file)
# TODO: Documentation:
'''
https://stackoverflow.com/questions/3898572/what-is-the-standard-python-docstring-format
https://numpydoc.readthedocs.io/en/latest/
https://www.python.org/dev/peps/pep-0257/
'''

import pandas as pd
import importlib
import openpyxl

TEST_CASE_FILENAME = "MiniMilestone_TestCases.xlsx"
SOLN_FILENAME_SUFFIX = "_SOLUTION"  # E.g. MM04_SOLUTION.py
INSTRUCTIONS_SHEETNAME = "Instructions"  # Name of sheet within TEST_CASE_FILENAME containing instructions
DELIMITER = ";"


def select_sheet(sheet_names_df):
    """
    Allows user to select a sheet from the TCWB for updating

    Parameters
    ----------
    sheet_names_df: Dataframe containing names of sheets in TCWB

    Returns
    -------
    Name of selected sheet within TCWB
    """
    sheet_names_df = sheet_names_df[sheet_names_df['Sheet Name'] != INSTRUCTIONS_SHEETNAME]  # Remove instructions sheet
    print(sheet_names_df, "\n")

    try:
        chosen_index = int(input("Please select the row number of the sheet you'd like to update: "))

        if chosen_index not in sheet_names_df.index:
            raise ValueError

        output = sheet_names_df.loc[chosen_index].values[0]
    except ValueError:
        print("Try again. Please choose the appropriate integer corresponding to the sheet you would like to update.\n")
        output = select_sheet(sheet_names_df)

    return output


def perform_test(parameters, function, solution_module):
    """
    Retrieves the output of a function from the solution script when the test case parameters are passed

    Parameters
    ----------
    parameters: Inputs from test case worksheet; type int/float/string (one input or multiple delimited values)
    function: Function to test
    solution_module: Solution module from which to retrieve function

    Returns
    -------
    Output(s) of function
    """
    for item in [parameters, function, solution_module]:
        if pd.isna(item):
            raise TypeError("Encountered empty input cell in workbook; check that input cells are completely filled")

    if parameters == "None":  # Lack of parameters must be indicated by the word 'None' instead of a blank cell
        parameters_list = []
    elif isinstance(parameters, str):
        parameters_list = [eval(i) for i in parameters.split(DELIMITER)]
    elif isinstance(parameters, int) or isinstance(parameters, float):  # ints and floats are recognized by Pandas
        parameters_list = [parameters]
    else:
        raise TypeError("Unknown parameters datatype for perform_test()")

    output = getattr(solution_module, function)(*parameters_list)  # Pass parameters into function

    return output


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
    solution_module = importlib.import_module(chosen_sheet + "_SOLUTION")  # Import appropriate solution module

    # Fill 'Outputs' column of selected sheet
    test_cases_df['Outputs'] = test_cases_df.apply(lambda x: perform_test(x['Inputs'], x['Function'], solution_module),
                                                   axis=1)

    writer = pd.ExcelWriter(TEST_CASE_FILENAME, engine='openpyxl', mode='a')

    book = openpyxl.load_workbook(TEST_CASE_FILENAME)  # Load existing sheets
    book.remove(book[chosen_sheet])  # Remove original sheet
    writer.book = book  # Update writer's book

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

    chosen_sheet_name = select_sheet(sheet_names_df)
    perform_tests(test_case_xl, chosen_sheet_name)

    print("*" * 75)
    print(f"Update complete. Check {TEST_CASE_FILENAME}. Press enter to quit.")
    input()


main()
