import warnings

from TestCaseWorksheet import TestCaseWorksheet
from Workbook import Workbook


class TestCaseWorkBook(Workbook):

    def __init__(self, path):
        super().__init__(path)

        self.instructions_sheet = "Instructions"
        self.non_test_sheets = [self.instructions_sheet]  # TODO: Support multiple non_test_sheets
        self.test_sheet_names_df = self.sheet_names_df[self.sheet_names_df['Sheet Name'] != self.instructions_sheet]

        self.update_worksheets_list()
        self.verify_testcases_sheets()

    def update_worksheets_list(self):
        for index, worksheet in enumerate(self.worksheets):
            if worksheet.name in self.test_sheet_names_df.values.flatten():
                self.worksheets[index] = TestCaseWorksheet(self, worksheet.name)

    def get_test_case_worksheets(self):
        return [worksheet for worksheet in self.worksheets if isinstance(worksheet, TestCaseWorksheet)]

    def select_testcase_sheets(self):
        """
        Allows user to select a sheet from the TCWB for updating

        Parameters
        ----------
        sheet_names_df: Dataframe containing names of sheets in TCWB

        Returns
        -------
        List of selected sheet names
        """
        self.display_test_sheets()

        chosen_index = input("Please select the row number of the sheet you'd like to update. If you would like to "
                             "update ALL sheets, enter 'all': ").strip()
        print("")

        if chosen_index == "all":
            # Select all sheet names; flattens numpy N-dimensional array
            return self.get_test_case_worksheets()

        else:
            try:
                chosen_index = int(chosen_index)
                if chosen_index not in self.sheet_names_df.index:
                    raise ValueError
            except ValueError:
                print("Please choose an appropriate option.\n")
                return self.select_sheets()

            selected_sheet_name = self.sheet_names_df.loc[chosen_index].values[0]
            return [self.test_cases_worksheets[selected_sheet_name]]

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
            warnings.warn(">>>> Warning: Missing instructions sheet in test case excel file <<<<<< \n")

        return True
