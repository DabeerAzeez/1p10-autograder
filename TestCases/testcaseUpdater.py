"""
Welcome to testcaseUpdater
author: Dabeer Abdul-Azeez (abdulazd@mcmaster.ca)

This script automatically determines the appropriate outputs for testcases which are listed in an excel file (the
"test case workbook" or TCWB) and then populates the file appropriately. The completed TCWB can then be used for
comparing student submissions to the correct answers.

Notes:
- This version uses xlrd v1.2.0; newer versions do not support xlsx files
- Don't have any excel files open otherwise permission errors will occur!
- The inputs in the TCWB are assumed to be using python syntax (e.g. 4**2 instead of 4^2)
"""

# TODO: Don't use old xlrd (https://stackoverflow.com/questions/65250207/pandas-cannot-open-an-excel-xlsx-file)

import pandas as pd
import importlib
import openpyxl

TEST_CASE_FILENAME = "MiniMilestone_TestCases.xlsx"
DELIMITER = ";"

test_case_xl = pd.ExcelFile(TEST_CASE_FILENAME)
sheet_names_df = pd.DataFrame(test_case_xl.sheet_names, columns=['Sheet Name'])


def select_sheet():
    """
    :return: Name of selected sheet within test case workbook
    """
    print(sheet_names_df, "\n")
    chosen_index = int(input("Please select the row number of the sheet you'd like to update: "))
    print()
    return sheet_names_df.loc[chosen_index].values[0]


def perform_test(parameters, function, solution_module):
    """
    :param parameters: Parameters from 'Inputs' column of test case worksheet; type int or string, string could be one
                       input or multiple delimited values
    :param function: Function to run the test on
    :param solution_module: Solution file module from which to retrieve function
    :return: output(s) of function
    """
    if isinstance(parameters, str):
        parameters_list = [eval(i) for i in parameters.split(DELIMITER)]

        if len(parameters_list) > 1:  # Handle multiple comma-separated inputs
            output = getattr(solution_module, function)(*parameters_list)
        else:
            output = getattr(solution_module, function)(parameters_list[0])

    elif isinstance(parameters, int) or isinstance(parameters, float):
        output = getattr(solution_module, function)(parameters)

    else:
        raise TypeError("Unknown parameters datatype for perform_test()")

    return output


def count_inputs(parameters):
    if isinstance(parameters, int) or isinstance(parameters, float):
        return 1
    else:
        return len(parameters.split(DELIMITER))


def perform_tests(chosen_sheet):
    """
    Auto-fills '# Inputs' and 'Outputs' columns of selected sheet in test cases workbook by passing the inputs through
    the appropriate functions from the appropriates Python solution file.
    :param chosen_sheet: Chosen sheet of test cases workbook
    """
    test_cases_df = pd.read_excel(test_case_xl, sheet_name=chosen_sheet)  # Read chosen sheet
    solution_module = importlib.import_module(chosen_sheet + "_SOLUTION")  # Import appropriate solution module

    # Fill 'Outputs' and '# Inputs' columns of selected sheet
    test_cases_df['Outputs'] = test_cases_df.apply(lambda x: perform_test(x['Inputs'], x['Function'], solution_module),
                                                   axis=1)
    test_cases_df['# Inputs'] = test_cases_df.apply(lambda x: count_inputs(x['Inputs']), axis=1)

    # Write dataframe content to excel file
    writer = pd.ExcelWriter(TEST_CASE_FILENAME, engine='openpyxl')  # TODO: Test without openpyxl
    book = openpyxl.load_workbook(TEST_CASE_FILENAME)  # Load existing sheets
    book.remove(book[chosen_sheet])  # Remove original sheet
    writer.book = book  # Update writer's book

    test_cases_df.to_excel(writer, chosen_sheet, index=False)

    try:
        writer.save()
    except PermissionError:
        raise PermissionError("Access denied when writing to excel file; try closing all excel files and restarting.")

    writer.close()


def main():
    print("Welcome to the testcaseUpdater. Below are the extracted sheets from the test case spreadsheet.\n")

    chosen_sheet_name = select_sheet()
    perform_tests(chosen_sheet_name)

    print(f"Update complete. Check {TEST_CASE_FILENAME}. Press enter to quit.")
    input()


main()
