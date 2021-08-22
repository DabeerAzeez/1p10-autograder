"""
1P10 Autograder, created by Dabeer Abdul-Azeez (abdulazd@mcmaster.ca) with help from Natalia Maximo
(https://github.com/taliamax)

Runs PyTest unit tests on student submissions, compiling the grades into a .csv file for easy
uploading to a Brightspace Learning Management System. Also generates a .csv file in case the
professor wants to send the grades in bulk via email (compatible with Mail Merge in Microsoft
Outlook).
"""

import importlib
import pathlib
import time
from unittest import mock
import sys
import re
from typing import Union, Tuple, Optional

import pytest
import click
import pandas as pd  # type: ignore

CLASSLIST_CSV_FILENAME = "_Classlist.csv"  # Name of class list downloaded from Brightspace class
MAX_STUDENT_POINTS = 100
CURRENT_PATH = pathlib.Path('.')


@click.command()
@click.argument('prefix')
def main(prefix: str):
    """
    Runs the autograder
    :param prefix: Prefix denoting the specific assignment being marked
    """
    students_graded = 0

    students_directory = f"{prefix}_submissions"
    solutions_module = f"{prefix}_solutions"

    classlist_df = pd.read_csv(CLASSLIST_CSV_FILENAME)

    check_missing_files_and_directories(students_directory)
    allowed_student_types = find_allowed_student_types(prefix)

    print("Starting Autograder...")
    print("*" * 20)
    start_time = time.time()

    for submission in CURRENT_PATH.glob(f"{students_directory}/{prefix}_*.py"):
        student_id, student_type = student_info_from_filestem(prefix, submission.stem)

        # Verify student file names
        verified = verify_student_filename(student_id, student_type, classlist_df,
                                           allowed_student_types, submission)
        if not verified:
            continue

        # Execute tests and write output into a text file for each student submission
        test_file = f"{prefix}_test_{student_type}" if student_type else f"{prefix}_test"

        with open(f"{students_directory}/{submission.stem}-out.txt", "w",
                  encoding='UTF-8') as output_file:
            sys.stdout = output_file
            execute_tests(submission.stem, test_file, students_directory, solutions_module)
            sys.stdout = sys.__stdout__
            print(f"Submission graded: {submission}")
            students_graded += 1

    if students_graded > 0:
        classlist_df_graded = process_outputs(students_directory, prefix, classlist_df)
        build_grades_csv_for_brightspace(prefix, classlist_df_graded)
        build_mail_merge_csv(prefix, classlist_df_graded)

    print("*" * 20)
    print(f"Autograder graded {students_graded} submissions in {time.time() - start_time} seconds.")


def find_allowed_student_types(prefix):
    """
    Find student types for which there are unit test files created.
    :param prefix: Prefix denoting the specific assignment being marked
    :return: set of allowed student types
    """
    allowed_student_types = set()
    if pathlib.Path(f"{prefix}_test.py").exists():
        allowed_student_types.add(None)
    else:
        for test_file in CURRENT_PATH.glob(f"{prefix}_test_*.py"):
            allowed_student_types.add(test_file.stem.split("_")[-1])
    if len(allowed_student_types) == 0:
        raise FileNotFoundError("No test files found for the selected assignment.")
    return allowed_student_types


def check_missing_files_and_directories(students_directory):
    """
    Checks for missing directories or files
    :param students_directory: Directory of student submissions
    """
    if not pathlib.Path(students_directory).exists():
        raise NotADirectoryError(f"Missing student submissions directory: /{students_directory}")
    if not list(CURRENT_PATH.glob(f"{students_directory}/*.py")):
        raise FileNotFoundError("Missing student Python submissions in appropriate submissions "
                                "directory.")


def verify_student_filename(student_id, student_type, classlist_df, allowed_student_types,
                            submission):
    if student_id is False or student_type is False:
        print("Submission name does not match expected pattern and will not be graded: " + str(
            submission))
        return False

    if f"#{student_id}" not in classlist_df['Username'].values:
        print("Unrecognized student ID: " + str(
            student_id) + " is not in the classlist and will not be graded.")
        return False

    if student_type not in allowed_student_types:
        print(f"Unrecognized student type for submission: {submission} cannot be graded.")
        return False

    return True


def execute_tests(
        stem: str,
        test_file: str,
        directory: str,
        solutions_module: str):
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


def process_outputs(
        students_directory: str,
        prefix: str,
        classlist_df):
    """
    Processes the output files generated when executing the PyTest tests to determine and collect
    the student's grade.
    :param students_directory: Directory containing student submissions
    :param prefix: Prefix denoting the specific assignment being marked
    :param classlist_df: Dataframe containing the class list from Brightspace
    :return: Class list dataframe with grades added for all students
    """
    classlist_df.insert(3, 'Grade', 0)

    for output_file in CURRENT_PATH.glob(f"{students_directory}/*-out.txt"):
        student_id, student_type = student_info_from_filestem(prefix, output_file.stem.rstrip(
            '-out'))
        with open(output_file, encoding='UTF-8') as file:
            data = file.read().splitlines()

        test_result_regex = re.compile(r'\S+_GRADE([\d]+)(\[.+])? (PASSED|FAILED)')
        total_grade = unscaled_grade = 0

        # Extract the grade from the lines of the PyTest output, adding the grade if the test passed
        for line in data:
            match = re.match(test_result_regex, line)
            if match:
                total_grade += int(match.group(1))
                unscaled_grade += int(match.group(1)) if match.group(3) == "PASSED" else 0

        scaled_grade = round(unscaled_grade / total_grade * MAX_STUDENT_POINTS)
        classlist_df.loc[classlist_df.Username == f"#{student_id}", 'Grade'] = scaled_grade

        submission_file = f"{students_directory}/{prefix}_{student_id}_{student_type}.py" \
            if student_type else f"{students_directory}/{prefix}_{student_id}.py"
        add_feedback_to_submission(scaled_grade, submission_file)

    return classlist_df


def add_feedback_to_submission(
        grade: int,
        submission_filename: str):
    """
    Insert grade feedback to the top of a student Python submission using a multi-line comment
    :param grade: Student's assignment grade
    :param submission_filename: Student's submission file
    """
    with open(submission_filename, encoding='UTF-8') as submission_file:
        content = submission_file.read()

    with open(submission_filename, "w", encoding='UTF-8') as submission_file:
        sys.stdout = submission_file
        print("'''")
        print("Hello, this is your autograder score, see below.")
        print(f"Score: {grade}/{MAX_STUDENT_POINTS}")
        print("If you would like to discuss your score, please contact prof1p10@mcmaster.ca")
        print("'''")
        print("\n")
        print(content)
        sys.stdout = sys.__stdout__


def build_grades_csv_for_brightspace(
        prefix: str,
        classlist_df_graded):
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


def build_mail_merge_csv(
        prefix: str,
        classlist_graded_df):
    """
    Create a .csv file with student names, emails, and grades, compatible for sending out the grades
    in bulk via email (e.g., via a mail merge in Outlook)
    :param prefix: Prefix denoting the specific assignment being marked
    :param classlist_graded_df: Class list dataframe with grades fully added
    :return:
    """
    mail_merge_csv_filename = f"{prefix}_mail_merge.csv"

    del classlist_graded_df["End-of-Line Indicator"]
    classlist_graded_df['Username'] = classlist_graded_df['Username'].apply(lambda x: x.lstrip("#"))
    classlist_graded_df['Grade'] = classlist_graded_df['Grade'].apply(
        lambda grade: f"{grade}/{MAX_STUDENT_POINTS}")
    classlist_graded_df.insert(1, 'Email', classlist_graded_df["Username"] + "@mcmaster.ca")
    classlist_graded_df.to_csv(mail_merge_csv_filename, index=False)


def student_info_from_filestem(prefix: str,
                               stem: str) -> Tuple[Union[str, bool], Optional[Union[str, bool]]]:
    """
    Extract student information from the filestem of a submission file
    :param prefix: Prefix denoting the specific assignment being marked
    :param stem: Stem of student submission file
    """

    filename_regex = re.compile(prefix + r'_([a-zA-Z0-9]*)(_[\w]*)?')
    # Example file names: MM04_abdulazd_StudentA.py, MM04_awani3_StudentB.py, MM04_beshaj2.py

    match = re.match(filename_regex, stem)
    if match:
        student_id = match.group(1).lower()
        student_type = match.group(2).lstrip('_') if match.group(2) else None
        return student_id, student_type

    return False, False


if __name__ == "__main__":
    main()
