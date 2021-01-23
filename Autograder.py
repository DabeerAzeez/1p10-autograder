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
# TODO: Test an object-oriented lab

import pandas as pd
import os
import utils
import time

CLASSLIST_FILENAME = "Classlist.csv"
GRADES_FILENAME = "Computing {} Grades.csv"
TESTCASES_PATH = "TestCases/MiniMilestone_TestCases.xlsx"
SUBMISSION_PATH = "./Computing {} Submission Files/"  # {} to be replaced by specific Mini-Milestone (e.g. MM04)
FEEDBACK_PATH = "./Computing {} Feedback Files/"


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

    def __init__(self, milestone_num):
        self.milestone_num = milestone_num

        try:
            self.testcases_sheet = pd.read_excel(TESTCASES_PATH, sheet_name=milestone_num)
            print("Found test cases excel file. Extracted sheet: " + milestone_num, flush=True)
            self.verify_testcases_sheet()
        except FileNotFoundError:
            raise FileNotFoundError("Missing test cases excel file.")

    def verify_testcases_sheet(self):
        utils.verify_testcases_sheet(self.testcases_sheet, self.milestone_num)

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

        # TODO: Fix int(input()) causing all tests to fail

        error_flag = False

        try:
            # Override built-in input() function to prevent program halt (students should avoid these within functions
            exec(student_code, {'input': override_input})  # Preliminary check
        except SyntaxError:
            feedback_list.append("A SyntaxError is preventing your file from being compiled")
            error_flag = True
        except ValueError:  # In case input statement results in ValueError
            feedback_list.append("A ValueError is preventing your file from being compiled")
            error_flag = True
        except Exception as e:
            feedback_list.append("An unexpected error is preventing your file from being compiled: " + str(e))
            error_flag = True

        if override_input.called:
            feedback_list.append("You shouldn't have input statements!")

        if error_flag:
            # Compilation errors result in a zero
            feedback_list.append("You have received a grade of zero.")
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
                    exec(student_code + "\n" + test_code, {'input': override_input})
                except NameError:
                    feedback_str = "Testcase: " + row['Command'] + " results in a name error. Something is not defined."
                except Exception as e:  # Bare except necessary to catch whatever error might occur in the student file
                    feedback_str = "Testcase: " + row['Command'] + " outputs an error: " + str(e)
                else:
                    if dont_test:
                        feedback_str = "Testcase: " + row['Command'] + " ran with no errors."
                    else:
                        # Calculate score
                        student_output = test_output[0] if len(test_output) else "No student output"

                        if student_output == correct_output:
                            test_score = row['Weight']
                            feedback_str = "Correct!"
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
                                    feedback_str = "Correct!"
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


def check_student_weights(autograder):
    # total points per student type (averaged over number of student types within test case sheet)
    student_types = list(autograder.testcases_sheet.Student.drop_duplicates())
    student_weights = set()

    for student_type in student_types:
        student_weight = sum(autograder.testcases_sheet[autograder.testcases_sheet.Student == student_type]['Weight'])
        student_weights.add(student_weight)

    if len(student_weights) > 1:
        print("Warning: Student Types have unequal weighting in testcases, so they will have different maximum points.")
        input("Press enter to continue. ")

    return student_weights


def grade_submissions(milestone_num, sub_path):
    """
    - Loops through submissions directory.
    - Compiles and executes each python file.
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

    student_weights = check_student_weights(autograder)
    total = max(student_weights)

    print("*" * 75)
    print("Beginning grading...")
    print("-" * 20)

    # Go through all python files in submission directory
    python_files = [file for file in sorted(os.listdir(sub_path)) if file.endswith(".py")]
    if len(python_files) == 0:
        raise FileNotFoundError("No submission files found!")

    for filename in python_files:  # Sample filename: abdulazd_MM04_StudentA.py

        filename_sections = filename.split("_")
        if len(filename_sections) == 1:
            raise ValueError("No submission files with underscore separator found.")

        # TODO: Add more error handling for student file names
        username = "#" + filename_sections[0]  # Pound symbol is to match Avenue classlist format
        current_student_type = filename_sections[2].lstrip("Student").rstrip(".py")  # Student A / B, etc.

        utils.disable_print()
        feedback, score = autograder.grade_submission(sub_path, filename, current_student_type)
        utils.enable_print()

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
    try:
        classlist = pd.read_csv(CLASSLIST_FILENAME)  # csv from Avenue in the format Username|Last Name|First Name
    except FileNotFoundError:
        raise FileNotFoundError("Missing classlist CSV.")

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
        raise NotADirectoryError("Mini-Milestone " + lab + " submission directory not found.")

    feedback_path = FEEDBACK_PATH.format(lab)
    if not os.path.exists(feedback_path):
        os.makedirs(feedback_path)

    results = grade_submissions(lab, sub_path)
    build_for_avenue(results, lab)
    append_feedback(lab, results, sub_path, feedback_path)
    num_subs = sum(filename.endswith(".py") for filename in sorted(os.listdir(sub_path)))  # TODO: Count submissions more accurately

    print("*" * 75)
    print("Grading complete")
    print("Autograder took {} seconds for {} submissions".format(time.time() - start, num_subs))


if __name__ == "__main__":
    main()
