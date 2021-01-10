"""
1P10 Autograder Python Script

Original Author: Basem Yassa <yassab@mcmaster.ca>
Adapted by: Dabeer Abdul-Azeez <abdulazd@mcmaster.ca> for use in marking the 1P10 iBioMed Computing Labs

Requirements to run this script:
- Class list csv file containing (Username | Last Name | First Name | End-of-Line Indicator)
    - This should be exported from the Avenue grade book for the class (select NO assignments when doing this)
- Test cases spreadsheet composed of individual sheets containing testcases for each mini milestone
    - See the "_Instructions" sheet included in the test cases workbook for information on how to write test cases
- Directory containing student .py files

This script will:
- Grade the listed functions in the test cases spreadsheet for all submissions in the submission directory
    - The autograder is intended to mark *helper* functions; *not* the main() function (that requires manual revision)
- Add feedback as a multi-line comment within the submitted files
- Generate a feedback folder wherein feedback-modified submissions will be stored (can be reuploaded to Avenue)
- Create a grades csv file which can be uploaded to Avenue to update the gradebook
"""
# TODO: Parameterize test case workbook column headers

import pandas as pd
import os
from utils import check_called, disable_print, enable_print
import time

CLASSLIST_FILENAME = "Classlist.csv"
GRADES_FILENAME = "Computing {} Grades.csv"
TESTCASES_PATH = "TestCases/MiniMilestone_TestCases.xlsx"
SUBMISSION_PATH = "./Computing {} Submission Files/"  # {} to be replaced by specific Mini-Milestone (e.g. MM04)
FEEDBACK_PATH = "./Computing {} Feedback Files/"


class Autograder:
    """
    Autograder Object to mark individual submissions
        
    Attributes
    --------
    database: Lab testcase info stored as a Pandas dataframe.
    tolerance: set to 0.00001% to avoid floating point errors.
    
    Methods
    --------
    grade_testcase(self, x, lower, upper, score, points)
        Runs assetion test and returns testcase score. 
    
    tol(self, value)
        Returns the upper and lower tolerance bounds for value.
    
    test(self, expected, actual, score, points)    
        tests that expected == actual and returns the students score according to the "points" that assertion is worth.

    run_tests(self, sub_path, filename, student_type):
        Runs tests from test case workbook on student code. Returns feedback strings and total score.
    """

    def __init__(self, milestone_num):
        self.milestone_num = milestone_num
        self.database = pd.read_excel(TESTCASES_PATH, sheet_name=milestone_num)
        self.tolerance = 0.0000001

    @staticmethod
    def grade_testcase(x, lower, upper, score, points):
        """
        Returns
        -------
        score: Testcase score.

        Inputs
        -------
        x: Actual output
        Lower: Expected output lower bound.
        upper: Expected output upper bound.
        score: Current score.
        points: Testcase points.
        """
        try:
            assert lower <= x <= upper
            score += points
        except AssertionError:
            score = score

        return score

    def tol(self, value):
        """
        Returns
        -------
        [upperTolerance, lowerTolerance]: Upper and lower bounds.

        
        Inputs
        -------
        value: value to be tested.
        """
        upper_tolerance = value * (1 + self.tolerance)
        lower_tolerance = value * (1 - self.tolerance)
        if value >= 0:  # accounts for negative numbers
            return [lower_tolerance, upper_tolerance]
        else:
            return [upper_tolerance, lower_tolerance]

    def test(self, expected, actual, score, points):
        """
        Returns
        -------
        score: Test score.

        
        Inputs
        -------
        expected: Autograder's output.
        actual: Student's output.
        score: Current score.
        points: Testcase points.
        """
        if type(expected) is list or type(expected) is tuple:
            # tests tuples and lists by recursively calling "test" and applying a tolerance to...
            # ...each entry in a list/ tuple and adding "points" to "temp" each time an entry...
            # ...passes the assertion test. Once it has gone through each entry it adds "points" to "score" if every ...
            # ...if every entry in the list/ tuple was correct.
            # If the list/ tuple is empty and is supposed to be empty then "points" is added to "score"

            if len(actual) == len(expected):
                temp = 0
                for i in range(len(expected)):
                    temp = self.test(actual[i], expected[i], temp, points)
                if len(expected) == 0:
                    score += points
                else:
                    score += (temp // (points * len(expected))) * points

        elif type(expected) is str:
            lower = upper = expected  # Strings
            score = self.grade_testcase(actual, lower, upper, score, points)

        else:
            lower, upper = self.tol(expected)
            score = self.grade_testcase(actual, lower, upper, score, points)

        return score

    def run_tests(self, sub_path, filename, student_type):
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
            content = f.read()

        total = 0
        feedback = []

        # Override built-in input() function to prevent program halt (students should avoid these within functions)
        @check_called
        def input(string=""):
            return "You shouldn't have input statements!"

        try:
            exec(content)  # Execute student code to import objects into local namespace
        # except SyntaxError:
        #     compilation_error_msg = "Program does not compile. You have received a grade of zero"
        #
        #     if username in list(results.Username):  # Account for multiple submissions
        #         results.loc[results.Username == username, :] = [username, filename, 0, total, compilation_error_msg]
        #     else:
        #         results.loc[len(results)] = [username, filename, 0, total, compilation_error_msg]
        #
        #     sys.stdout = system_info  # Enable print()
        #     print(username[1:], "graded. (Received Zero)")
        #     continue
        except ValueError:  # In case input statement results in ValueError
            if input.called:
                feedback.append("You shouldn't have input statements!")
            else:
                feedback.append("Unknown error occurred while running your program...attempting to test functions.")

        for index, row in self.database.iterrows():
            feedback_str = ""
            score = 0
            output = []  # List works more easily with exec() variable modification

            if row['Student'] != student_type:  # Only perform a test case if the student is the right type
                continue

            test_code = "output.insert(0,str(" + row['Command'] + "))"
            correct_output = row['Outputs']

            try:
                exec(test_code)
                if output[0] == correct_output:
                    score = row['Weight']
                    feedback_str = "Correct!"
                else:
                    score = 0
                    feedback_str = "Testcase: " + row['Command'] + " gives an incorrect output."
            except NameError:
                score = 0
                feedback_str = "Testcase: " + row['Command'] + " results in a name error. Function not defined."
            except Exception as e:  # Bare except necessary to catch whatever error might occur in the student file
                score = 0
                feedback_str = "Testcase: " + row['Command'] + " outputs an error: " + str(e)

            score_msg = "({0}/{1}) ".format(score, row['Weight'])
            total += score

            feedback.append(score_msg + feedback_str)

        return feedback, total


def grade_submissions(milestone_num, sub_path):
    """
    - Loops through submissions directory.
    - Compiles and executes each python file.
    - Runs Autograder methods on the functions/classes defined.
    - Returns names, filenames, grades, and feedback in a dataframe
    
    Returns
    -------
    results: Raw results dataframe in the format, Name|File Name|Grade|Out of|Comments.

    Inputs
    -------
    lab: lab number.
    path: Student submissions folder path.
    """
    autograder = Autograder(milestone_num)
    results = pd.DataFrame(columns=["Username", "File Name", "Grade", "Out of", "Comments"])

    # total points per student type (averaged over number of student types within test case sheet)
    total = sum(autograder.database.Weight) / len(autograder.database.Student.drop_duplicates())

    # Go through all python files in submission directory
    python_files = [file for file in sorted(os.listdir(sub_path)) if file.endswith(".py")]
    for filename in python_files:  # Sample filename: abdulazd_MM04_StudentA.py

        filename_sections = filename.split("_")
        username = "#" + filename_sections[0]  # Pound symbol is to match Avenue classlist format
        current_student_type = filename_sections[2].lstrip("Student").rstrip(".py")  # Student A / B, etc.

        disable_print()

        feedback, score = autograder.run_tests(sub_path, filename, current_student_type)  # Run tests

        enable_print()

        if feedback:
            feedback_string = "\n".join(feedback)
        else:
            feedback_string = "No functions found!"

        if username in list(results.Username):  # Account for multiple submissions
            results.loc[results.Username == username, :] = [username, filename, score, total, feedback_string]
        else:
            results.loc[len(results)] = [username, filename, score, total, feedback_string]

        print(username[1:], "graded.")

    results.to_csv("Computing {} Raw Results.csv".format(milestone_num), index=False)
    return results


def add_name(results):
    """
    Adds student name to inputted dataframe based by performing an inner join with an extracted classlist.
    
    Returns
    -------
    final: Dataframe in the format, Username|Name|Last Name|First Name|Grade|Out of|Comments.

    Inputs
    -------
    results: Raw results dataframe.
    """
    classlist = pd.read_csv(CLASSLIST_FILENAME)  # csv extracted from avenue in the format Username|Last Name|First Name
    name_added = pd.merge(classlist, results, on=['Username'])

    return name_added


def build_for_avenue(final, lab):
    """
    Reformats the dataframe and outputs it to an uploadable csv file.
    
    Returns
    -------
    None

    Inputs
    -------
    final: Dataframe in the format, Username|Name|Last Name|First Name|Grade|Out of|Comments.
    lab: Lab number
    """
    if str(lab) in "234":
        grade_item = "Computing Lab {0} Points Grade <Numeric MaxPoints:{1}>".format(lab, final["Out of"][0])
    else:
        grade_item = "Computing Lab {0} - Objective Points Grade <Numeric MaxPoints:{1}>".format(lab,
                                                                                                 final["Out of"][0])

    avenue_upload = final.loc[:, ["Username", "Grade"]]
    avenue_upload.rename(columns={"Grade": grade_item}, inplace=True)
    avenue_upload["End-of-Line Indicator"] = "#"
    avenue_upload.to_csv(GRADES_FILENAME.format(lab), index=False)


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
            "office hours or email prof1p10@mcmaster.ca"

    body += "\nHave a wonderful day,\nYour Friendly Neighbourhood Bot"

    body += "\n'''"

    return body


def append_feedback(lab, results, path, feedback_path):
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
    results = add_name(results)  # Add 'First Name' and 'Last Name' columns for personalized messages

    for i in range(len(results)):
        name, feedback = results["First Name"][i], results["Comments"][i]
        msg = build_feedback(name, lab, feedback)
        file = path + results["File Name"][i]
        feedback_file = feedback_path + results["File Name"][i]
        with open(file, "r", encoding="utf8") as f:
            content = f.read()

        with open(feedback_file, "w", encoding="utf8") as f:
            f.write(msg + "\n\n\n\n\n" + content)


def main():
    start = time.time()
    lab = input("Please input mini-milestone number (e.g. MM04): ")

    sub_path = SUBMISSION_PATH.format(lab)
    if not os.path.exists(sub_path):
        raise NotADirectoryError("Missing directory: " + sub_path)

    feedback_path = FEEDBACK_PATH.format(lab)
    if not os.path.exists(feedback_path):
        os.makedirs(feedback_path)

    print("\nBeginning grading...")
    print("*" * 75)

    results = grade_submissions(lab, sub_path)
    build_for_avenue(results, lab)
    append_feedback(lab, results, sub_path, feedback_path)
    num_subs = sum(filename.endswith(".py") for filename in sorted(os.listdir(sub_path)))

    print("*" * 75)
    print("Grading complete")
    print("Autograder took {} seconds for {} submissions".format(time.time() - start, num_subs))


if __name__ == "__main__":
    main()
