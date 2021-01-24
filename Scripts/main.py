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
- Generate a feedback folder wherein feedback-modified submissions will be stored (can be re-uploaded to Avenue)
- Create a grades csv file which can be uploaded to Avenue to update the grade book
"""
# TODO: Parameterize test case workbook column headers
# TODO: Start another thread to check for timeouts

import time

import utils
from Autograder import Autograder


def build_grades_csv_for_brightspace(autograder):
    """
    Takes an autograder's results dataframe and modifies it to a csv file which can be uploaded to a
    D2L Brightspace class assignment to update student marks.

    Inputs
    -------
    autograder: An autograder which already has a populated results dataframe
    """
    if autograder.results_df.empty:
        raise ValueError("Autograder with empty results Dataframe detected; "
                         "grade some submissions with the autograder before creating a Brightspace csv file")

    grade_header = "Mini-Milestone {} - Objective Points Grade <Numeric MaxPoints:{}>" \
        .format(autograder.MILESTONE_NUM, autograder.max_student_points)

    brightspace_upload_df = autograder.results_df.loc[:, ["Username", "Grade"]]
    brightspace_upload_df.rename(columns={"Grade": grade_header}, inplace=True)
    brightspace_upload_df["End-of-Line Indicator"] = "#"  # Brightspace requirement for grade upload csv files
    brightspace_upload_df.to_csv(autograder.GRADES_CSV_FILENAME, index=False)


def main():
    milestone_num = input("Please input mini-milestone number (e.g. MM04): ")

    utils.print_message_in_characters("PROGRAM START", "*", 75)

    start = time.time()
    autograder = Autograder(milestone_num)
    autograder.find_submissions()
    autograder.grade_submissions()
    build_grades_csv_for_brightspace(autograder)
    end = time.time()

    utils.print_message_in_characters("PROGRAM END", "*", 75)
    print("Program took {} seconds for {} submissions".format(end - start, autograder.num_submissions))


if __name__ == "__main__":
    main()
