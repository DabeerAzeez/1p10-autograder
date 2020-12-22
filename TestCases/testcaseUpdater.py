"""
Welcome to testcaseUpdater
author: Dabeer Abdul-Azeez (abdulazd@mcmaster.ca)

This script automatically determines the appropriate outputs for testcases which are listed in an excel file and then
populates said excel file appropriately. The completed excel file can then be used for comparing student submissions to
the correct answers.

Notes:
- This version uses xlrd v1.2.0; newer versions do not support xlsx files, and this file cannot work around those yet
- Don't have any excel files open otherwise permission errors may occur!
"""

# TODO: Don't use old xlrd (https://stackoverflow.com/questions/65250207/pandas-cannot-open-an-excel-xlsx-file)

import pandas as pd
import importlib

TEST_CASE_FILENAME = "MiniMilestone_TestCases.xlsx"

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
    :param parameters: Parameters to be passed to function
    :param function: Function to run the test on
    :param solution_module: Solution file module from which to retrieve function
    :return: output(s) of function
    """
    params_list = [eval(i) for i in parameters.split(",")]  # eval() assumes inputs in workbook use python syntax
    output = getattr(solution_module, function)(*params_list)  # pass parameters into function from solution module

    return output


def perform_tests(chosen_sheet):
    """
    Auto-fills '# Inputs' and 'Outputs' columns of selected sheet in test cases workbook by passing the inputs through
    the appropriate functions from the appropriates Python solution file.
    :param chosen_sheet: Chosen sheet of test cases workbook
    """
    test_cases_df = pd.read_excel(test_case_xl, sheet_name=chosen_sheet)
    solution_module = importlib.import_module(chosen_sheet + "_SOLUTION")

    # Fill 'Outputs' and '# Inputs' columns of selected sheet
    test_cases_df['Outputs'] = test_cases_df.apply(lambda x: perform_test(x['Inputs'], x['Function'], solution_module),
                                                   axis=1)
    test_cases_df['# Inputs'] = test_cases_df.apply(lambda x: len(x['Inputs'].split(",")), axis=1)

    # Write dataframe content to excel file
    writer = pd.ExcelWriter(TEST_CASE_FILENAME, engine='openpyxl')  # TODO: Test without openpyxl
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

    print(f"Update complete. Check {TEST_CASE_FILENAME}.")


main()
