"""
1P10 Autograder Python script

Original Author: Basem Yassa <yassab@mcmaster.ca>
Adapted by: Dabeer Abdul-Azeez <abdulazd@mcmaster.ca> for use in marking the 1P10 iBioMed Computing Labs

Required Files / Directories to be placed in root directory beside script:
- Class list csv file containing (Username | Last Name | First Name | End-of-Line Indicator)
    - This should be exported from Avenue the grade book
- Test cases spreadsheet containing individual sheets containing testcases for each mini milestone
    - See the "_Instructions" sheet included in the test cases workbook for information on how to write test cases
- Directory containing student .py files

This autograder will:
- Grade all submissions in the submission directory
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
            assert x >= lower and x <= upper
            score += points
        except:
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
        upperTolerance = value * (1 + self.tolerance)
        lowerTolerance = value * (1 - self.tolerance)
        if value >= 0:  # accounts for negative numbers
            return [lowerTolerance, upperTolerance]
        else:
            return [upperTolerance, lowerTolerance]

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

    def markFunction(self, score, func):
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
            input = functiondb.Inputs[i]
            output = functiondb.Outputs[i]

            if isinstance(input, str):
                parameters_list = [eval(i) for i in functiondb.Inputs[i].split(Autograder.DELIMITER)]
            elif isinstance(input, int) or isinstance(input, float):
                parameters_list = [input]
            else:
                raise TypeError("Unknown function input: " + input)

            try:
                student_answer = func(*parameters_list)
            except:
                feedback.append("Testcase input: " + str(parameters_list) + " outputs an error")
                continue

            if isinstance(output, int) or isinstance(output, float):
                expected = output
            elif isinstance(output, str):
                expected = eval(output)  # TODO: accommodate string outputs
            else:
                raise TypeError("Unknown function output: " + output)

            score = self.test(expected, student_answer, score, functiondb.Weight[i])

            if temp == score:  # If score did not update
                feedback.append("Testcase input: " + str(parameters_list) + " has an incorrect Output")
            else:
                temp = score

        feedback = list(dict.fromkeys(feedback))  # Remove duplicate comments

        feedback_str = func.__name__ + ": ({0}/{1})\n\t".format(score, total) + (
            ",\n\t".join(feedback) if feedback != [] else "Correct!")

        return feedback_str, score

    def markFunctions(self, *funcs):
        """
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
            feedback_str, score = self.markFunction(0, func)
            total += score
            feedback.append(feedback_str)
        return feedback, total

    def markFile(self, filename):  # TODO
        return

    def markObject(self, obj):  # TODO
        return


def gradeSubmissions(lab, path):
    """
    - Loops through submissions directory.
    - Compiles and executes each python file.
    - Runs Autograder methods on the functions/classes defined.
    - Returns names, filnames, grades, and feedback in a dataframe
    
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
    systemInfo = sys.stdout  # To enable and disable print()
    AG = Autograder(lab)
    total = sum(AG.database.Weight)
    results = pd.DataFrame(columns=["Name", "File Name", "Grade", "Out of", "Comments"])
    if lab == "2":
        def input(string=""):
            from random import random
            return random() * 10
    else:
        def input(string=""):
            return "You've been bamboozled"
    for filename in sorted(os.listdir(path)):
        if not filename.endswith(".py"):
            continue
        name = filename.split(" - ")[1].rstrip(".py")
        with open(path + filename, encoding="utf8") as f:
            sys.stdout = open(os.devnull, 'w')  # Disable print()
            try:

                content = f.read()
                code = compile(content, path + filename, 'exec')
                temp = {"input": input}
                exec(code, temp)

            except SyntaxError:
                if name in list(results.Name):  # Account for multiple submissions
                    results.loc[results.Name == name, :] = [name, filename, 0, total,
                                                            "Program does not compile. You have recieved a grade of zero"]
                else:
                    results.loc[len(results)] = [name, filename, 0, total,
                                                 "Program does not compile. You have recieved a grade of zero"]
                sys.stdout = systemInfo  # Enable print()
                print(name, "graded. (Recieved Zero)")
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
            for func in list(AG.database.Function.drop_duplicates()):
                try:
                    funcs.append(temp[func])
                except KeyError:  # Function Misspelled or Does not exist
                    continue

        feedback, score = AG.markFunctions(*funcs)
        sys.stdout = systemInfo  # Enable print()
        if feedback:
            feedbackStr = "\n".join(feedback)
        else:
            feedbackStr = "No functions found!"
        if name in list(results.Name):  # Account for multiple submissions
            results.loc[results.Name == name, :] = [name, filename, score, total, feedbackStr]
        else:
            results.loc[len(results)] = [name, filename, score, total, feedbackStr]
        print(name, "graded.")

    results.to_csv("Computing {} Raw Results.csv".format(lab), index=False)
    return results


def addMacID(results):
    """
    Adds student MacID based by performing
    an inner join with an extracted classlist. 
    
    Author:
        Basem Yassa <yassab@mcmaster.ca>
    
    Returns
    -------
    final: Dataframe in the format, Username|Name|Last Name|First Name|Grade|Out of|Comments.

    Inputs
    -------
    results: Raw results dataframe.
    """
    classlist = pd.read_csv(CLASSLIST_FILENAME)  # csv extracted from avenue in the format Username|Last Name|First Name
    # Note the added (#) to usernames is to account for Avenue's upload format
    classlist["Name"] = classlist["First Name"] + " " + classlist["Last Name"]
    results = results[["Name", "Grade", "Out of", "Comments"]]

    final = pd.merge(classlist, results, on=['Name'])

    return (final)


def buildForAvenue(final, lab):
    """
    Reformats the dataframe and outputs it to an uploadable csv file.
    
    Author:
        Basem Yassa <yassab@mcmaster.ca>
    
    Returns
    -------
    None

    Inputs
    -------
    final: Dataframe in the format, Username|Name|Last Name|First Name|Grade|Out of|Comments.
    lab: Lab number
    """
    if str(lab) in "234":
        gradeItem = "Computing Lab {0} Points Grade <Numeric MaxPoints:{1}>".format(lab, final["Out of"][0])
    else:
        gradeItem = "Computing Lab {0} - Objective Points Grade <Numeric MaxPoints:{1}>".format(lab, final["Out of"][0])
    avenueUpload = final.drop(columns=["Out of", "Comments", "Name", "First Name", "Last Name"])
    avenueUpload.rename(columns={"Grade": gradeItem}, inplace=True)
    avenueUpload["End-of-Line Indicator"] = "#"
    avenueUpload.to_csv(GRADES_FILENAME.format(lab), index=False)


def buildFeedback(name, lab, feedback):
    """
    Building feedback string to be inserted in student submissions.
    
    Author:
        Basem Yassa <yassab@mcmaster.ca>
    
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


def appendFeedback(lab, results, path, feedbackPath):
    """
    Loops through student submission and creates a copy with feedback inserted at the top.
    
    Author:
        Basem Yassa <yassab@mcmaster.ca>
    
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
    for i in range(len(results)):
        name, feedback = results["Name"][i].split()[0], results["Comments"][i]
        msg = buildFeedback(name, lab, feedback)
        file = path + results["File Name"][i]
        feedbackFile = feedbackPath + results["File Name"][i]
        with open(file, "r", encoding="utf8") as f:
            content = f.read()

        with open(feedbackFile, "w", encoding="utf8") as f:
            f.write(msg + "\n\n\n\n\n" + content)
    print("Done")


def main():
    import os
    import time
    start = time.time()
    lab = input("Please input mini-milestone number (e.g. MM04): ")
    feedbackPath = FEEDBACK_PATH.format(lab)
    subPath = SUBMISSION_PATH.format(lab)  # Make sure files are stored in this folder
    if not os.path.exists(feedbackPath):
        os.makedirs(feedbackPath)
    results = gradeSubmissions(lab, subPath)
    final = addMacID(results)
    buildForAvenue(final, lab)
    appendFeedback(lab, results, subPath, feedbackPath)
    numSubs = sum(filename.endswith(".py") for filename in sorted(os.listdir(subPath)))
    print("Autograder took {} seconds for {} submissions".format(time.time() - start, numSubs))


if __name__ == "__main__":
    main()
