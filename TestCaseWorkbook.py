import pandas as pd


class TestCaseWorkBook:
    def __init__(self, path):
        self.WORKBOOK_PATH = path
        self.WORKBOOK_XL = pd.ExcelFile(path)

        self.sheet_names_df = pd.DataFrame(self.WORKBOOK_XL.sheet_names, columns=['Sheet Name'])

        self.instructions_sheet = "Instructions"
        self.optional_sheets = [self.instructions_sheet]

        self.command_col = "Command"
        self.dont_test_col = "DontTest"
        self.student_col = "Student"
        self.weight_col = "Weight"
        self.outputs_col = "Outputs"

        self.columns = [self.command_col, self.dont_test_col, self.student_col, self.weight_col, self.outputs_col]
        self.req_columns = [self.command_col, self.student_col, self.weight_col, self.outputs_col]
        self.optional_columns = [self.dont_test_col]

