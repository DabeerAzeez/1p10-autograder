import os


class Submission:
    def __init__(self, path):
        self.path = path
        self.file_name = self.path  # TODO: Make this extract the file name if the path is long
        self.contents = ""
        self.file_type = os.path.splitext(self.path)[-1]

    def extract_contents(self):
        with open(self.path) as f:
            self.contents = f.read()
