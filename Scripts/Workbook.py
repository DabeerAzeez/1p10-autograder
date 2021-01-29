import pandas as pd
import openpyxl
from Worksheet import Worksheet


class Workbook:
    def __init__(self, path):
        self.path = path
        self.WORKBOOK_XL = ""
        self.openpyxl_workbook = ""
        self.excel_writer = ""
        self.sheet_names_df = ""
        self.worksheets = []

        self.load_excel_file()

    def load_excel_file(self):
        self.WORKBOOK_XL = pd.ExcelFile(self.path)
        self.openpyxl_workbook = openpyxl.load_workbook(self.path)
        self.excel_writer = pd.ExcelWriter(self.path, engine='openpyxl', mode='a')

        self.sheet_names_df = pd.DataFrame(self.WORKBOOK_XL.sheet_names, columns=['Sheet Name'])
        self.worksheets = {sheet_name: Worksheet(self, sheet_name)
                           for sheet_name in self.sheet_names_df.values.flatten()}

    def display_sheets(self):
        print(self.sheet_names_df, "\n")

    def get_sheet_by_name(self, sheet_name):
        return self.worksheets[sheet_name]

    def get_sheets(self):
        return self.worksheets

    def select_sheets(self):
        self.display_sheets()

        chosen_index = input("Please select the row number of the sheet you'd like to update. If you would like to "
                             "update ALL sheets, enter 'all': ").strip()

        if chosen_index == "all":
            return self.get_sheets()
        else:
            try:
                if chosen_index in self.sheet_names_df.index:
                    return self.sheet_names_df.loc[chosen_index].values[0]
            except ValueError:
                print("Please choose an appropriate option.\n")
                return self.select_sheets()

        return None
