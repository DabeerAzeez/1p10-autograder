# TODO: Display sheets available in testcases.xlsx (https://stackoverflow.com/questions/17977540/pandas-looking-up-the-list-of-sheets-in-an-excel-file)
# TODO: Allow user to choose one of the sheets
# TODO: Extract inputs and method names from appropriate sheet of testcase spreadsheet (pd.read_excel('example.xlsx',sheet_name=[...])
# TODO: Import methods from appropriate solution file
# TODO: Populate "# of inputs" and "outputs" columns in appropriate sheet of testcase spreadsheet

# TODO: Don't use old version of xlrd (https://stackoverflow.com/questions/65250207/pandas-cannot-open-an-excel-xlsx-file)

import pandas as pd

TEST_CASE_FILENAME = "MiniMilestone_TestCases.xlsx"

test_case_xl = pd.ExcelFile(TEST_CASE_FILENAME)
sheet_names_df = pd.DataFrame(test_case_xl.sheet_names, columns=['Sheet Name'])

print(sheet_names_df)