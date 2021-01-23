import utils
import pandas as pd
import os

class Autograder:
    """
    Autograder Class to mark individual submissions

    Class Attributes
    ----------------
    TOLERANCE: set to 0.00001% to avoid floating point errors.

    Instance Attributes
    --------
    database: Lab testcase info stored as a Pandas dataframe.

    Methods
    --------
    within_tol(actual_value, expected_value)
        Returns a boolean if the actual value is within the Autograder's tolerance of the expected value

    test(self, expected, actual, score, points)
        tests that expected == actual and returns the students score according to the "points" that assertion is worth.

    grade_submission(self, sub_path, filename, student_type):
        Runs tests from test case workbook on student code. Returns feedback strings and total score.
    """

    TOLERANCE = 0.0000001
    CLASSLIST_FILENAME = "Classlist.csv"
    TESTCASES_XL_PATH = "TestCases/MiniMilestone_TestCases.xlsx"

    def __init__(self, milestone_num):
        self.GRADES_CSV_FILENAME = "Computing {} Grades.csv".format(milestone_num)
        self.SUBMISSION_PATH = "./Computing {} Submission Files/".format(milestone_num)
        self.FEEDBACK_PATH = "./Computing {} Feedback Files/".format(milestone_num)
        self.MILESTONE_NUM = milestone_num

        self.results_df = pd.DataFrame(columns=[''])
        self.num_submissions = 0

        try:
            self.testcases_sheet = pd.read_excel(Autograder.TESTCASES_XL_PATH, sheet_name=milestone_num)
            print("Found test cases excel file. Extracted sheet: " + milestone_num, flush=True)
            self.verify_testcases_sheet()
        except FileNotFoundError:
            raise FileNotFoundError("Missing test cases excel file.")

    def verify_testcases_sheet(self):
        utils.verify_testcases_sheet(self.testcases_sheet, self.MILESTONE_NUM)

    @staticmethod
    def within_tol(actual_value, expected_value):
        """Returns a boolean if the actual value is within the Autograder's tolerance of the expected value"""
        lower_bound = (1 - Autograder.TOLERANCE) * expected_value
        upper_bound = (1 + Autograder.TOLERANCE) * expected_value
        return True if lower_bound <= actual_value <= upper_bound else False

    def grade_submission(self, sub_path, filename, student_type):
        """
        Runs tests on provided student code based on their student type.

        Parameters
        ----------
        sub_path: Submission directory path
        filename: name of student's file
        student_type: character representing student type (e.g. "A" or "B")

        Returns
        -------
        feedback: List of feedback strings
        total: lab score
        """
        with open(sub_path + filename, encoding="utf8") as f:
            student_code = f.read()

        total_score = 0
        feedback_list = []

        @utils.check_called
        def override_input(string=""):
            return "You shouldn't have input statements!"

        error_flag = False

        try:
            # Override built-in input() function to prevent program halt (students should avoid these within functions
            exec(student_code, {'input': override_input})  # Preliminary check
        except SyntaxError:
            feedback_list.append("A SyntaxError is preventing your file from being compiled")
            error_flag = True
        except Exception as e:
            feedback_list.append("An unexpected error is preventing your file from being compiled: " + str(e))
            error_flag = True

        if override_input.called:
            feedback_list.append("You shouldn't have input statements!")

        if error_flag:
            # Compilation errors result in a zero
            feedback_list.append("An error occurred while compiling your code, so you have received a grade of zero.")
        else:
            # If the program compiled, run test cases
            for index, row in self.testcases_sheet.iterrows():
                test_score = 0
                test_output = []  # List mutates more easily via exec()
                try:
                    dont_test = row['DontTest'] == "x"
                except KeyError:
                    dont_test = False

                if dont_test:
                    test_code = row['Command']
                else:
                    test_code = "test_output.insert(0,str(" + row['Command'] + "))"  # TODO: Parameterize variable name

                if row['Student'] != student_type:  # Only perform a test case if the student is the right type
                    continue

                correct_output = row['Outputs']

                try:
                    gdict = globals()  # Inputting globals allows objects to be saved for later tests
                    gdict['input'] = override_input  # TODO: understand this
                    gdict['test_output'] = test_output

                    exec(student_code + "\n" + test_code, gdict)  # TODO: Avoid using newlines
                except NameError as e:
                    feedback_str = "Testcase: " + row['Command'] + " results in a name error: " + str(e)
                except Exception as e:  # Bare except necessary to catch whatever error might occur in the student file
                    feedback_str = "Testcase: " + row['Command'] + " outputs an error: " + str(e)
                else:
                    if dont_test:
                        feedback_str = "Command: " + row['Command'] + " ran with no errors."
                    else:
                        # Calculate score
                        student_output = test_output[0] if len(test_output) else "No student output"

                        if student_output == correct_output:
                            test_score = row['Weight']
                            feedback_str = "Testcase: " + row['Command'] + " gives the correct output!"
                        else:
                            try:
                                # Account for floating point errors if output should be numeric
                                correct_output = float(correct_output)
                                student_output = float(student_output)
                            except ValueError:
                                feedback_str = "Testcase: " + row['Command'] + " gives an incorrect output."
                            else:
                                if Autograder.within_tol(student_output, correct_output):
                                    test_score = row['Weight']
                                    feedback_str = "Testcase: " + row['Command'] + " gives the correct output!"
                                else:
                                    feedback_str = "Testcase: " + row['Command'] + " gives an incorrect output."
                finally:
                    if dont_test:
                        feedback_list.append(feedback_str)
                    else:
                        score_msg = "({0}/{1}) ".format(test_score, row['Weight'])
                        feedback_list.append(score_msg + feedback_str)

                    total_score += test_score

        return feedback_list, total_score

    def get_max_student_points(self):
        student_types = list(self.testcases_sheet.Student.drop_duplicates())
        student_weights = set()

        for student_type in student_types:
            student_weight = sum(self.testcases_sheet[self.testcases_sheet.Student == student_type]['Weight']
                                 .dropna())  # Sum all non-empty 'weight' entries with the correct student type
            student_weights.add(student_weight)

        if len(student_weights) > 1:
            print("Warning: Student Types have unequal weighting in testcases; they will have different maximum points."
                  " The highest maximum points among all students will be set as the maximum points for this run.")
            input("Press enter to continue. ")

        return max(student_weights)

    def grade_submissions(self):
        """
        - Loops through submissions directory.
        - Compiles and executes each python file
            - Each student submission is assumed to adhere to the following naming convention: MacID_MM##_StudentX.py
                - MacID is a string of letters and possibly numbers
                - ## represents an integer, depending on the milestone
                - X represents any letter; it denotes the student 'type' (i.e. what objectives they must accomplish)

        Returns
        -------
        - Names, filenames, grades, maximum grade, and feedback in a dataframe
        - Number of submissions graded

        Inputs
        -------
        milestone_num: milestone number (e.g. MM04).
        submission_path: Student submissions folder path for the corresponding milestone_num
        """
        results_df = pd.DataFrame(columns=["Username", "File Name", "Grade", "Out of", "Comments"])

        max_student_points = self.get_max_student_points()

        print("*" * 75)
        print("Beginning grading...")
        print("-" * 20)

        # All python files in the submission directory count as submissions
        submissions = [file for file in sorted(os.listdir(self.SUBMISSION_PATH)) if file.endswith(".py")]

        if len(submissions) == 0:
            raise FileNotFoundError("No submission files found!")

        self.num_submissions = len(submissions)

        # Grade each submission and update results dataframe with the student grade
        for submission in submissions:
            filename_sections = submission.split("_")
            if len(filename_sections) == 1:
                raise ValueError("Submission file missing underscore separator: " + str(submission))

            # TODO: Add more error handling for student file names
            username = "#" + filename_sections[0]  # Pound symbol is to match Avenue classlist format
            current_student_type = filename_sections[2].lstrip("Student").rstrip(".py")  # Student A / B, etc.

            utils.disable_print()
            feedback, score = self.grade_submission(self.SUBMISSION_PATH, submission, current_student_type)
            utils.enable_print()

            if feedback:
                feedback_string = "\n".join(feedback)
            else:
                feedback_string = "No functions found!"

            if username in list(results_df.Username):  # Account for multiple submissions
                results_df.loc[results_df.Username == username, :] = [username, submission, score, max_student_points,
                                                                      feedback_string]
            else:
                results_df.loc[len(results_df)] = [username, submission, score, max_student_points, feedback_string]

            print(username[1:], "graded.")

        self.results_df = results_df
        self.append_feedback_to_student_files()

    def append_feedback_to_student_files(self):
        """
        Loops through student submission and creates a copy with feedback inserted at the top.

        Returns
        -------
        None

        Inputs
        -------
        lab: Lab number.
        results: Raw results dataframe.
        path: Student submissions folder path.
        feedbackPath: Student feedback folder path.
        """
        self.add_student_names_to_results_df()

        # Loop over results data frame, compile feedback, and write it into each student's file
        for i in range(len(self.results_df)):
            name = self.results_df["First Name"][i]
            feedback = self.results_df["Comments"][i]

            msg = self.build_feedback(name, self.MILESTONE_NUM, feedback)

            submission_file = self.SUBMISSION_PATH + self.results_df["File Name"][i]
            with open(submission_file, "r", encoding="utf8") as f:
                content = f.read()

            submission_file_with_feedback = self.FEEDBACK_PATH + self.results_df["File Name"][i]
            with open(submission_file_with_feedback, "w", encoding="utf8") as f:
                f.write(msg + content)

    def add_student_names_to_results_df(self):
        """
        Adds student name to inputted dataframe based by performing an inner join with an extracted classlist.

        Returns
        -------
        final: Dataframe in the format, Username|Name|Last Name|First Name|Grade|Out of|Comments.

        Inputs
        -------
        results: Raw results dataframe.
        """
        # Add 'First Name' and 'Last Name' columns (extracted from classlist) for personalized messages

        try:
            classlist_df = pd.read_csv(Autograder.CLASSLIST_FILENAME)
        except FileNotFoundError:
            raise FileNotFoundError("Missing classlist CSV.")

        self.results_df = pd.merge(classlist_df, self.results_df, on=['Username'])

    @staticmethod
    def build_feedback(name, lab, feedback):
        """
        Building feedback string to be inserted in student submissions.

        Returns
        -------
        body: Feedback string body.

        Inputs
        -------
        name: Student's firstname.
        lab: Lab number.
        feedback: Raw feedback string.
        """
        body = "'''\n"

        body += "Hello " + name + ",\n\nHere is Computing Lab {} feedback given by the autograder:\n\n".format(lab)

        body += feedback  # Insert feedback here

        body += "\n\n"

        body += "If you have any questions about your mark, please visit us \nduring " \
                "office hours or email prof1p10@mcmaster.ca\n"

        body += "\nHave a wonderful day,\nYour Friendly Neighbourhood Bot"

        body += "\n'''"

        body += "\n" * 5

        return body
