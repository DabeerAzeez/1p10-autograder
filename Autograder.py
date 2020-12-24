"""
1P10 Autograder Python Script

Original Author: Basem Yassa <yassab@mcmaster.ca>
Adapted by: Dabeer Abdul-Azeez <abdulazd@mcmaster.ca> for use in marking the 1P10 iBioMed Computing Labs

Requirements to run this script:
- Class list csv file containing (Username | Last Name | First Name | End-of-Line Indicator)
    - This should be exported from Avenue the grade book
- Test cases spreadsheet containing individual sheets containing testcases for each mini milestone
    - See the "_Instructions" sheet included in the test cases workbook for information on how to write test cases
- Directory containing student .py files

This script will:
- Grade the listed functions in the test cases spreadsheet for all submissions in the submission directory
    - The autograder is intended to mark *helper* functions; *not* the main() function (that requires manual revision)
- Add feedback as a multi-line comment within the submitted files
- Generate a feedback folder wherein feedback-modified submissions will be stored (can be reuploaded to Avenue)
- Create a grades csv file which can be uploaded to Avenue to update the gradebook
"""

import pandas as pd

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
    
    markFunction(self, score, func)
        Marks an individual function and returns function feedback and score.
        
    markFunctions(self, *funcs)
        Marks the functions inputted and returns feedback and total score.
        
    markFile(self, file)
        TODO
    
    markObject(self, obj)
        TODO
    
    """

    DELIMITER = ";"

    def __init__(self, milestone_num):
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

    def mark_function(self, score, func):
        """
        Returns
        -------
        feedback_str: Function feedback string.
        score: Function score.

        
        Inputs
        -------
        score: current score.
        func: Function to be tested.
        """

        functiondb = self.database.loc[self.database["Function"] == func.__name__]  # Function database
        total = sum(functiondb.Weight)
        temp = 0
        feedback = []
        first = functiondb.index[0]
        last = first + len(functiondb.Function)

        for i in range(first, last):
            inputs = functiondb.Inputs[i]
            output = functiondb.Outputs[i]

            if type(inputs) is str:
                parameters_list = [eval(i) for i in functiondb.Inputs[i].split(Autograder.DELIMITER)]
                display_input = str(parameters_list)
            elif type(inputs) is int or type(inputs) is float:
                parameters_list = [inputs]
                display_input = str(parameters_list[0])
            else:
                raise TypeError("Unknown function input: " + inputs)

            try:
                student_answer = func(*parameters_list)
            except:  # Bare except necessary to catch whatever error might occur in the student file
                feedback.append("Testcase input: " + display_input + " outputs an error")
                continue

            if type(output) is int or type(output) is float:
                expected = output
            elif type(output) is str:
                expected = eval(output)  # TODO: accommodate string outputs
            else:
                raise TypeError("Unknown function output: " + output)

            score = self.test(expected, student_answer, score, functiondb.Weight[i])

            if temp == score:  # If score did not update
                feedback.append("Testcase input: " + display_input + " has an incorrect Output")
            else:
                temp = score

        feedback = list(dict.fromkeys(feedback))  # Remove duplicate comments

        feedback_str = func.__name__ + ": ({0}/{1})\n\t".format(score, total) + (
            ",\n\t".join(feedback) if feedback != [] else "Correct!")

        return feedback_str, score

    def mark_functions(self, *funcs):
        """
        Marks functions, providing a total score and feedback

        Returns
        -------
        feedback: Function(s) feedback string.
        total: lab score.

        Inputs
        -------
        funcs: Function(s) to be tested.
        """
        total = 0
        feedback = []
        for func in funcs:
            feedback_str, score = self.mark_function(0, func)
            total += score
            feedback.append(feedback_str)
        return feedback, total

    def mark_file(self, filename):  # TODO
        return

    def mark_object(self, obj):  # TODO
        return


def grade_submissions(lab, path):
    """
    - Loops through submissions directory.
    - Compiles and executes each python file.
    - Runs Autograder methods on the functions/classes defined.
    - Returns names, filenames, grades, and feedback in a dataframe
    
    Author:
        Basem Yassa <yassab@mcmaster.ca>
    
    Returns
    -------
    results: Raw results dataframe in the format, Name|File Name|Grade|Out of|Comments.


    Inputs
    -------
    lab: lab number.
    path: Student submissions folder path.
    """
    import os, sys
    system_info = sys.stdout  # To enable and disable print()
    autograder = Autograder(lab)
    total = sum(autograder.database.Weight) / len(autograder.database.Student.drop_duplicates())
    results = pd.DataFrame(columns=["Username", "File Name", "Grade", "Out of", "Comments"])

    def input(string=""):  # Override built-in input() function to prevent program from stopping
        return "You've been bamboozled"

    # Extract relevant functions based on the student type
    all_functions = list(autograder.database.Function.drop_duplicates())
    student_funcs_dict = dict.fromkeys(all_functions)

    for function in all_functions:  # Connect functions with appropriate students
        rows = autograder.database.loc[autograder.database['Function'] == function]
        associated_student = rows.iloc[0].Student
        student_funcs_dict[function] = associated_student

    # Go through all files in submission directory
    for filename in sorted(os.listdir(path)):  # Sample filename: abdulazd_MM04.py
        if not filename.endswith(".py"):
            continue

        filename_sections = filename.split("_")
        username = "#" + filename_sections[0]  # Pound symbol is to match Avenue classlist format
        current_student_type = filename_sections[2].lstrip("Student").rstrip(".py")  # Student A / B, etc.

        with open(path + filename, encoding="utf8") as f:
            sys.stdout = open(os.devnull, 'w')  # Disable print()
            try:

                content = f.read()
                code = compile(content, path + filename, 'exec')
                temp = {"input": input}
                exec(code, temp)

            except SyntaxError:
                compilation_error_msg = "Program does not compile. You have recieved a grade of zero"

                if username in list(results.Username):  # Account for multiple submissions
                    results.loc[results.Username == username, :] = [username, filename, 0, total, compilation_error_msg]
                else:
                    results.loc[len(results)] = [username, filename, 0, total, compilation_error_msg]

                sys.stdout = system_info  # Enable print()
                print(username[1:], "graded. (Recieved Zero)")
                continue
            except:  # Account for students who have garbage in their submission
                try:
                    extractedCode = content[content.find("# Implementation"):content.find("Testing")]
                    extractedCode = extractedCode if extractedCode != "" else content
                    code = compile(extractedCode, path + filename, 'exec')
                    temp = {"input": input}
                    exec(code, temp)
                except:
                    pass  # If absolutely nothing works in their file
            funcs = []

            relevant_functions = []
            for func, student_type in student_funcs_dict.items():
                if student_type == current_student_type:
                    relevant_functions.append(func)

            for func in relevant_functions:
                try:
                    funcs.append(temp[func])
                except KeyError:  # Function Misspelled or Does not exist
                    continue

        feedback, score = autograder.mark_functions(*funcs)
        sys.stdout = system_info  # Enable print()
        if feedback:
            feedback_string = "\n".join(feedback)
        else:
            feedback_string = "No functions found!"
        if username in list(results.Username):  # Account for multiple submissions
            results.loc[results.Username == username, :] = [username, filename, score, total, feedback_string]
        else:
            results.loc[len(results)] = [username, filename, score, total, feedback_string]
        print(username[1:], "graded.")

    results.to_csv("Computing {} Raw Results.csv".format(lab), index=False)
    return results


def add_name(results):
    """
    Adds student name to inputted dataframe based by performing
    an inner join with an extracted classlist.
    
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
        grade_item = "Computing Lab {0} - Objective Points Grade <Numeric MaxPoints:{1}>".format(lab, final["Out of"][0])

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
    import os
    import time

    start = time.time()
    lab = input("Please input mini-milestone number (e.g. MM04): ")

    sub_path = SUBMISSION_PATH.format(lab)
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
