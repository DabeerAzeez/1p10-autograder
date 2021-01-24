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
# TODO: Modularize instructions sheet names to include other excluded sheets
# TODO: Only show sheets based on a RegEx match to the sheet name
# TODO: Test 'None' as an output

import utils
from TestCaseWorkbook import TestCaseWorkBook

TEST_CASE_WORKBOOK_PATH = "TestCases/MiniMilestone_TestCases.xlsx"
SOLUTION_FILENAME_SUFFIX = "_SOLUTION"  # E.g. MM04_SOLUTION.py


def main():
    test_case_workbook = TestCaseWorkBook(TEST_CASE_WORKBOOK_PATH)

    print("Welcome to the testcaseUpdater. Below are the extracted sheets from the test case spreadsheet.\n")

    test_case_workbook.select_sheets()

    utils.disable_print()

    for selected_sheet in test_case_workbook.selected_sheets:
        test_case_workbook.perform_tests(selected_sheet)

    utils.enable_print()

    print("*" * 75)
    print(f"Update complete. Check {TEST_CASE_WORKBOOK_PATH}. Press enter to quit.")
    input()


main()
