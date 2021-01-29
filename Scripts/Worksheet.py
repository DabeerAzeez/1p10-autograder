import pandas as pd


class Worksheet:
    def __init__(self, workbook, sheet_name):
        self.workbook = workbook
        self.name = sheet_name
        self.sheet_df = pd.read_excel(self.workbook.path, sheet_name=self.name)

    def write_to_workbook(self):
        writer = self.workbook.excel_writer
        book = self.workbook.openpyxl_workbook

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
