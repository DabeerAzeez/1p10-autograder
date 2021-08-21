"""
1P10 Autograder, created by Dabeer Abdul-Azeez (abdulazd@mcmaster.ca) with help from Natalia Maximo
(https://github.com/taliamax)

Runs PyTest unit tests on student submissions, compiling the grades into a .csv file for easy uploading to a
Brightspace Learning Management System. Also generates a .csv file in case the professor wants to send the grades in
bulk via email (compatible with Mail Merge in Microsoft Outlook).
"""

import importlib
import pathlib
import time
import unittest.mock as mock
import pytest
import sys
import click
import re
import pandas as pd

CLASSLIST_CSV_FILENAME = "_Classlist.csv"  # Name of class list downloaded from Brightspace class
MAX_STUDENT_POINTS = 100
CURRENT_PATH = pathlib.Path('.')


# TODO: Add typing, add error handling
# TODO: Comment code


@click.command()
@click.argument('prefix')
def main(prefix):
    students_directory = f"{prefix}_submissions"
    solutions_module = f"{prefix}_solutions"

    classlist_df = pd.read_csv(CLASSLIST_CSV_FILENAME)

    print("Starting Autograder...")
    start_time = time.time()

    for file in CURRENT_PATH.glob(f"{students_directory}/*.py"):
        student_id, student_type = student_info_from_filestem(file.name)

        if student_id is False or student_type is False:
            print("Filename does not match expected pattern and will not be graded: " + str(file))
            continue

        if not f"#{student_id}" in classlist_df['Username'].values:
            print("Unrecognized student ID: " + student_id + " is not found in the classlist and will not be graded.")
            continue

        test_file = f"{prefix}_test_{student_type}" if student_type else f"{prefix}_test"

        with open(f"{students_directory}/{file.stem}-out.txt", "w") as f:
            # Execute tests and write output into a text file for each student submission
            sys.stdout = f
            execute_tests(file.stem, test_file, students_directory, solutions_module)
            sys.stdout = sys.__stdout__

    classlist_df_graded = process_outputs(students_directory, prefix, classlist_df)
    build_grades_csv_for_brightspace(prefix, classlist_df_graded)
    build_mail_merge_csv(prefix, classlist_df_graded)

    print(f"Autograder completed in {time.time() - start_time} seconds.")


def execute_tests(stem, test_file, directory, solutions_module):
    """
    Executes PyTest tests for a student submission
    :param stem: File stem for the student Python submission in the submission directory
    :param test_file: Python file containing boilerplate code and PyTest tests
    :param directory: Directory containing student submissions
    :param solutions_module: File stem for the Python file containing assignment solutions
    """
    print(f"Running tests on file {stem}.py....")

    with mock.patch(f"{test_file}.solutions_module") as mock_solutions:
        mock_solutions.return_value = importlib.import_module(solutions_module, ".")
        with mock.patch(f"{test_file}.assignment_module") as mock_assignment:
            mock_assignment.return_value = importlib.import_module(f".{stem}", directory)
            pytest.main([__file__, f"{test_file}.py", "-vvl"])


def process_outputs(students_directory, prefix, classlist_df):
    """
    Processes the output files generated when executing the PyTest tests to determine and collect the student's grade.
    :param students_directory: Directory containing student submissions
    :param prefix: Prefix denoting the specific assignment being marked
    :param classlist_df: Dataframe containing the class list from Brightspace
    :return: Class list dataframe with grades added for all students
    """
    classlist_df.insert(3, 'Grade', 0)

    for file in CURRENT_PATH.glob(f"{students_directory}/*-out.txt"):
        student_id, student_type = student_info_from_filestem(file.stem.rstrip('-out'))
        with open(file) as f:
            data = f.read().splitlines()

        test_result_regex = re.compile(r'\S+_GRADE([\d]+)(\[.+])? (PASSED|FAILED)')

        total_grade = grade = 0

        for line in data:
            match = re.match(test_result_regex, line)
            if match:
                total_grade += int(match.group(1))
                grade += int(match.group(1)) if match.group(3) == "PASSED" else 0

        scaled_grade = round(grade / total_grade * MAX_STUDENT_POINTS)
        classlist_df.loc[classlist_df.Username == f"#{student_id}", 'Grade'] = scaled_grade

        submission_file = f"{students_directory}/{prefix}_{student_id}_{student_type}.py" if student_type else \
            f"{students_directory}/{prefix}_{student_id}.py"
        add_feedback_to_submission(scaled_grade, submission_file, total_grade)

    return classlist_df


def add_feedback_to_submission(grade, submission_file, total_grade):
    """
    Insert grade feedback to the top of a student Python submission using a multi-line comment
    :param grade: Student's assignment grade
    :param submission_file: Student's submission file
    :param total_grade: Total grade for the assignment
    """
    with open(submission_file) as f:
        content = f.read()
        sys.stdout = open(submission_file, "w")
        print("'''")
        print("Hello, this is your autograder score, see below.")
        print(f"Score: {grade}/{total_grade}")
        print("If you would like to discuss your score, please contact prof1p10@mcmaster.ca")
        print("'''")
        print("\n")
        print(content)
        sys.stdout = sys.__stdout__


def build_grades_csv_for_brightspace(prefix, classlist_df_graded):
    """
    Build a grades .csv file for uploading to Brightspace
    :param prefix: Prefix denoting the specific assignment being marked
    :param classlist_df_graded: Class list dataframe with grades fully added
    """
    grades_csv_filename = f"{prefix}_grades.csv"
    grade_header = "Mini-Milestone {} - Objective Points Grade <Numeric MaxPoints:{}>" \
        .format(prefix, MAX_STUDENT_POINTS)

    brightspace_upload_df = classlist_df_graded.copy()
    brightspace_upload_df.rename(columns={"Grade": grade_header}, inplace=True)
    brightspace_upload_df.to_csv(grades_csv_filename, index=False)


def build_mail_merge_csv(prefix, classlist_graded_df):
    """
    Create a .csv file with student names, emails, and grades, compatible for sending out the grades in bulk via
    email (e.g., via a mail merge in Outlook)
    :param prefix: Prefix denoting the specific assignment being marked
    :param classlist_graded_df: Class list dataframe with grades fully added
    :return:
    """
    mail_merge_csv_filename = f"{prefix}_mail_merge.csv"

    del classlist_graded_df["End-of-Line Indicator"]
    classlist_graded_df['Username'] = classlist_graded_df['Username'].apply(lambda x: x.lstrip("#"))
    classlist_graded_df['Grade'] = classlist_graded_df['Grade'].apply(lambda grade: f"{grade}/{MAX_STUDENT_POINTS}")
    classlist_graded_df.insert(1, 'Email', classlist_graded_df["Username"] + "@mcmaster.ca")
    classlist_graded_df.to_csv(mail_merge_csv_filename, index=False)


def student_info_from_filestem(stem):
    """
    Extract student information from the filestem of a submission file
    :param stem: Stem of student submission file
    """

    filename_regex = re.compile(r'MM\d+_([a-z0-9]*)(_[\w]*)?')
    # Example file names: MM04_abdulazd_StudentA.py, MM04_awani3_StudentB.py, MM04_beshaj2.py

    match = re.match(filename_regex, stem)
    if match:
        student_id = match.group(1)
        student_type = match.group(2).lstrip('_') if match.group(2) else None
        return student_id, student_type
    else:
        return False, False


if __name__ == "__main__":
    main()
