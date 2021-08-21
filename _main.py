import importlib
import pathlib
import time
import unittest.mock as mock
import pytest
import sys
import click
import re
import pandas as pd

CLASSLIST_CSV_FILENAME = "_Classlist.csv"
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
            sys.stdout = f
            execute_tests(file.stem, test_file, students_directory, solutions_module)
            sys.stdout = sys.__stdout__

    classlist_df_graded = process_outputs(students_directory, prefix, classlist_df)
    build_grades_csv_for_brightspace(prefix, classlist_df_graded)
    build_mail_merge_csv(prefix, classlist_df_graded)

    print(f"Autograder completed in {time.time() - start_time} seconds.")


def execute_tests(stem, test_file, directory, solutions_module):
    print(f"Running tests on file {stem}.py....")

    with mock.patch(f"{test_file}.solutions_module") as mock_solutions:
        mock_solutions.return_value = importlib.import_module(solutions_module, ".")
        with mock.patch(f"{test_file}.assignment_module") as mock_assignment:
            mock_assignment.return_value = importlib.import_module(f".{stem}", directory)
            pytest.main([__file__, f"{test_file}.py", "-vvl"])


def process_outputs(students_directory, prefix, submissions_df):
    submissions_df.insert(3, 'Grade', 0)

    for file in CURRENT_PATH.glob(f"{students_directory}/*-out.txt"):
        student_id, student_type = student_info_from_filestem(file.stem.rstrip('-out'))
        with open(file) as f:
            data = f.read().splitlines()

        test_result_regex = re.compile(r'\S+_GRADE([\d]+)(\[.+])? (PASSED|FAILED)')

        total_grade = current_grade = 0

        for line in data:
            match = re.match(test_result_regex, line)
            if match:
                total_grade += int(match.group(1))
                current_grade += int(match.group(1)) if match.group(3) == "PASSED" else 0

        submissions_df.loc[submissions_df.Username == f"#{student_id}", 'Grade'] = \
            round(current_grade / total_grade * MAX_STUDENT_POINTS)

        submission_file = f"{students_directory}/{prefix}_{student_id}_{student_type}.py" if student_type else \
            f"{students_directory}/{prefix}_{student_id}.py"
        add_feedback_to_submission(current_grade, submission_file, total_grade)

    return submissions_df


def add_feedback_to_submission(current_grade, submission_file, total_grade):
    with open(submission_file) as f:
        content = f.read()
        sys.stdout = open(submission_file, "w")
        print("'''")
        print("Hello, this is your autograder score, see below.")
        print(f"Score: {current_grade}/{total_grade}")
        print("If you would like to discuss your score, please contact prof1p10@mcmaster.ca")
        print("'''")
        print("\n")
        print(content)
        sys.stdout = sys.__stdout__


def build_grades_csv_for_brightspace(prefix, submissions_df_graded):
    grades_csv_filename = f"{prefix}_grades.csv"
    grade_header = "Mini-Milestone {} - Objective Points Grade <Numeric MaxPoints:{}>" \
        .format(prefix, MAX_STUDENT_POINTS)

    brightspace_upload_df = submissions_df_graded.copy()
    brightspace_upload_df.rename(columns={"Grade": grade_header}, inplace=True)
    brightspace_upload_df.to_csv(grades_csv_filename, index=False)


def build_mail_merge_csv(prefix, classlist_graded_df):
    mail_merge_csv_filename = f"{prefix}_mail_merge.csv"

    del classlist_graded_df["End-of-Line Indicator"]
    classlist_graded_df['Username'] = classlist_graded_df['Username'].apply(lambda x: x.lstrip("#"))
    classlist_graded_df['Grade'] = classlist_graded_df['Grade'].apply(lambda grade: f"{grade}/{MAX_STUDENT_POINTS}")
    classlist_graded_df.insert(1, 'Email', classlist_graded_df["Username"] + "@mcmaster.ca")
    classlist_graded_df.to_csv(mail_merge_csv_filename, index=False)


def student_info_from_filestem(filename):
    filename_regex = re.compile(r'MM\d+_([a-z0-9]*)(_[\w]*)?')
    # Example file names: MM04_abdulazd_StudentA.py, MM04_awani3_StudentB.py, MM04_beshaj2.py

    match = re.match(filename_regex, filename)
    if match:
        student_id = match.group(1)
        student_type = match.group(2).lstrip('_') if match.group(2) else None
        return student_id, student_type
    else:
        return False, False


if __name__ == "__main__":
    main()
