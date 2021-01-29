from Submission import Submission
import re


class IBioSubmission(Submission):
    def __init__(self):
        super().__init__()

        self.mac_ID = ""
        self.student_type = ""
        self.mini_milestone = ""

        if self.verify_file_name_scheme(self.file_name):
            self.get_attributes()
        else:
            print("File " + self.file_name + " does not fit the IBio file name scheme.")

    @staticmethod
    def verify_file_name_scheme(file_name):
        return True if re.match("\w*_MM\d\d_Student[A-Z]", file_name) else False

    def get_attributes(self):
        self.mac_ID, self.student_type, self.mini_milestone = self.file_name.split("_").rstrip(".py")


