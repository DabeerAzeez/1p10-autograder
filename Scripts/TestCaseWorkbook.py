import openpyxl
import pandas as pd

import utils
from TestCaseWorksheet import TestCaseWorksheet


class TestCaseWorkBook:

    def __init__(self, path):
        self.WORKBOOK_PATH = path

        try:
            self.WORKBOOK_XL = pd.ExcelFile(self.WORKBOOK_PATH)
            self.openpyxl_workbook = openpyxl.load_workbook(self.WORKBOOK_PATH)
            self.excel_writer = pd.ExcelWriter(self.WORKBOOK_PATH, engine='openpyxl', mode='a')
        except FileNotFoundError:
            raise FileNotFoundError("Missing test cases excel file.")
        else:
            print("Found test cases excel file.")

        self.sheet_names_df = pd.DataFrame(self.WORKBOOK_XL.sheet_names, columns=['Sheet Name'])

        self.instructions_sheet = "Instructions"
        self.non_test_sheets = [self.instructions_sheet]  # TODO: Support multiple non_test_sheets

        self.test_sheet_names_df = self.sheet_names_df[self.sheet_names_df['Sheet Name'] != self.instructions_sheet]

        self.verify_testcases_sheets()

    def select_sheet(self, chosen_sheet_name):
        return TestCaseWorksheet(self, chosen_sheet_name)

    def select_sheets(self):
        """
        Allows user to select a sheet from the TCWB for updating

        Parameters
        ----------
        sheet_names_df: Dataframe containing names of sheets in TCWB

        Returns
        -------
        List of selected sheet names
        """
        selected_sheets = []
        self.display_test_sheets()

        chosen_index = input("Please select the row number of the sheet you'd like to update. If you would like to "
                             "update ALL sheets, enter 'all': ").strip()
        print("")

        if chosen_index == "all":
            # Select all sheet names; flattens numpy N-dimensional array
            utils.print_message_in_characters("EXTRACTING AND VERIFYING SHEETS...", "*", 75)
            for selected_sheet_name in self.test_sheet_names_df.values.flatten():
                selected_sheets.append(TestCaseWorksheet(self, selected_sheet_name))
            return selected_sheets

        else:
            try:
                chosen_index = int(chosen_index)
                if chosen_index not in self.sheet_names_df.index:
                    raise ValueError
            except ValueError:
                print("Please choose an appropriate option.\n")
                return self.select_sheets()

            selected_sheet_name = self.sheet_names_df.loc[chosen_index].values[0]
            utils.print_message_in_characters("EXTRACTING AND VERIFYING SHEETS...", "*", 75)
            return TestCaseWorksheet(self, selected_sheet_name)

    def display_test_sheets(self):
        print(self.test_sheet_names_df, "\n")

    def verify_testcases_sheets(self):
        """
        Verify that a Dataframe representing the names of the sheets in the test cases Excel file is correctly set up.

        Parameters
        ----------
        sheet_names_df: Dataframe to be tested

        Returns
        -------
        True if all tests pass
        """
        if self.instructions_sheet not in self.sheet_names_df.values:
            print(">>>> Warning: Missing instructions sheet in test case excel file <<<<<< \n")

        return True
