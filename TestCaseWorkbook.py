import pandas as pd
import openpyxl
import importlib

SOLUTION_FILENAME_SUFFIX = "_SOLUTION"  # E.g. MM04_SOLUTION.py


def import_solution(module_name, level):
    """
    Imports given module's methods into selected namespace of the file in which this is run. Adapted from
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


class TestCaseWorksheet:
    def __init__(self, test_case_workbook, chosen_sheet_name):
        self.name = chosen_sheet_name
        self.test_case_workbook = test_case_workbook
        self.sheet_df = pd.read_excel(self.test_case_workbook.WORKBOOK_PATH, sheet_name=self.name)
        print("Extracted sheet: '" + chosen_sheet_name + "'")

        self.COMMAND_COL = "Command"
        self.DONT_TEST_COL = "DontTest"
        self.STUDENT_COL = "Student"
        self.WEIGHT_COL = "Weight"
        self.OUTPUTS_COL = "Outputs"

        self.COLUMNS = [self.COMMAND_COL, self.DONT_TEST_COL, self.STUDENT_COL, self.WEIGHT_COL, self.OUTPUTS_COL]
        self.REQ_COLUMNS = [self.COMMAND_COL, self.STUDENT_COL, self.WEIGHT_COL, self.OUTPUTS_COL]
        self.REQ_FULL_COLUMNS = [self.COMMAND_COL, self.STUDENT_COL]
        self.OPTIONAL_COLUMNS = [self.DONT_TEST_COL]

        self.verify_self()

    def write_to_workbook(self):
        writer = pd.ExcelWriter(self.test_case_workbook.WORKBOOK_PATH, engine='openpyxl', mode='a')

        book = openpyxl.load_workbook(self.test_case_workbook.WORKBOOK_PATH)
        book.remove(book[self.name])  # Remove original sheet to prevent duplicates
        writer.book = book

        # Write updated test case sheet to excel file
        self.sheet_df.to_excel(writer, self.name, index=False)

        try:
            writer.save()
        except PermissionError:
            raise PermissionError(
                "Access denied when writing to excel file; try closing all excel files and restarting.")

        writer.close()

    def verify_self(self):
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
        print("Verifying test case worksheet '" + self.name + "' is set up properly...",
              flush=True)  # Flush prevents errors printing first

        for col in self.REQ_COLUMNS:
            if col not in self.sheet_df.columns:
                raise SyntaxError("Missing " + col + " column or column header in sheet " + self.name)

        for col in self.REQ_FULL_COLUMNS:
            if self.sheet_df[col].isna().any():
                raise SyntaxError("Missing at least one entry in " + col + " column of sheet " + self.name)

        # Check columns for appropriate types of inputs
        try:
            # Check for non-alphabetic entries in the 'Student' column
            if self.sheet_df[self.STUDENT_COL].apply(lambda x: not x.isalpha()).any():
                raise ValueError
        except (AttributeError, ValueError):
            raise ValueError("Non alphabetic character in Student column of sheet " + self.name)

        try:
            # Check for non-numeric entries in the 'Weight' column
            if self.sheet_df[self.WEIGHT_COL].apply(lambda x: not isinstance(x, (int, float))).any():
                raise ValueError
        except (AttributeError, ValueError):
            raise ValueError("Non-numeric character in Weight column of sheet " + self.name)

        try:
            # Check for numeric entries in the 'Command' column
            if self.sheet_df[self.COMMAND_COL].apply(lambda x: isinstance(x, (int, float))).any():
                raise ValueError
        except (AttributeError, ValueError):
            raise ValueError("Numeric character (not a command!) in Command column of sheet " + self.name)

        for col in self.sheet_df.columns:
            if col not in self.REQ_COLUMNS and col not in self.OPTIONAL_COLUMNS:
                raise ValueError("Unknown column \"" + str(col) + "\" found in test case worksheet.")

        if self.DONT_TEST_COL in self.sheet_df.columns:
            # Make sure 'test' rows have appropriate data in columns
            test_rows = self.sheet_df[self.sheet_df[self.DONT_TEST_COL].isnull()]
            if test_rows[self.WEIGHT_COL].isna().any():
                raise ValueError("Missing items in \"Weight\" column for rows to be tested for grades")
            # TODO: Check for missing 'output' column value in not DontTest rows

        print("Test case worksheet is properly set up.")
        return True

    def perform_tests(self):
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
            # TODO: Parameterize TestCases folder name
            import_solution("TestCases." + self.name + SOLUTION_FILENAME_SUFFIX, "global")
            # TODO: test local version
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(str(e) + " --> missing solution module for selected test case excel sheet")

        # Run test for each row
        for index, row in self.sheet_df.iterrows():
            # iterrows generator should not be used for large dataframes

            try:
                if row[self.DONT_TEST_COL] == "x":
                    # Run the command, but don't treat it like a test (don't record output)
                    test_code = row[self.COMMAND_COL]
                else:
                    test_code = f"row['{self.OUTPUTS_COL}'] " \
                                f"= str(" + row[self.COMMAND_COL] + ")"

            except KeyError:
                test_code = f"row['{self.OUTPUTS_COL}'] " \
                            f"= str(" + row[self.COMMAND_COL] + ")"

            try:
                exec(test_code)
            except Exception as e:
                row_num = index + 2  # Account for header row and zero-based array indexing
                raise Exception(str(e) + " --> exception occurred in sheet " + self.name +
                                " row " + str(row_num) + " of test cases excel file.")

            self.sheet_df.loc[index] = row  # Update test_cases dataframe with local row Series

        # TODO: Offload excel writing to another method

        # Remove original sheet to prevent duplicates
        self.test_case_workbook.openpyxl_workbook.remove(
            self.test_case_workbook.openpyxl_workbook[self.name])
        self.test_case_workbook.excel_writer.book = self.test_case_workbook.openpyxl_workbook

        self.sheet_df.to_excel(self.test_case_workbook.excel_writer, self.name, index=False)

        try:
            self.test_case_workbook.excel_writer.save()  # Write updated test case sheet to excel file
        except PermissionError:
            raise PermissionError(
                "Access denied when writing to excel file; try closing all excel files and restarting.")

        self.test_case_workbook.excel_writer.close()

        # Sort worksheets alphabetically
        # TODO: Sort sheets alphabetically without accessing a protected member
        # noinspection PyProtectedMember
        self.test_case_workbook.openpyxl_workbook._sheets.sort(key=lambda ws: ws.title)
        self.test_case_workbook.openpyxl_workbook.save(self.test_case_workbook.WORKBOOK_PATH)


class TestCaseWorkBook:

    def __init__(self, path):
        self.WORKBOOK_PATH = path
        self.WORKBOOK_XL = pd.ExcelFile(path)

        self.openpyxl_workbook = openpyxl.load_workbook(self.WORKBOOK_PATH)
        self.excel_writer = pd.ExcelWriter(self.WORKBOOK_PATH, engine='openpyxl', mode='a')
        self.sheet_names_df = pd.DataFrame(self.WORKBOOK_XL.sheet_names, columns=['Sheet Name'])
        self.selected_sheets = ""

        self.instructions_sheet = "Instructions"
        self.non_test_sheets = [self.instructions_sheet]  # TODO: Support multiple non_test_sheets

        self.test_sheet_names_df = self.sheet_names_df[self.sheet_names_df['Sheet Name'] != self.instructions_sheet]

        self.verify_testcases_sheets()

    def select_sheet(self, chosen_sheet_name):
        self.selected_sheets = TestCaseWorksheet(self, chosen_sheet_name)

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
        self.display_test_sheets()

        chosen_index = input("Please select the row number of the sheet you'd like to update. If you would like to "
                             "update ALL sheets, enter 'all': ").strip()

        if chosen_index == "all":
            # Select all sheet names; flattens numpy N-dimensional array
            self.selected_sheets = self.test_sheet_names_df.values.flatten()
            return

        try:
            chosen_index = int(chosen_index)
            if chosen_index not in self.sheet_names_df.index and chosen_index != -1:
                raise ValueError
        except ValueError:
            print("Please choose an appropriate option.\n")
            return self.select_sheets()

            selected_sheet_name = self.sheet_names_df.loc[chosen_index].values[0]
            return

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