import importlib
import pathlib
import unittest.mock as mock
import pytest
import sys
import click
import re
import pandas as pd

CLASSLIST_CSV_FILENAME = "_Classlist.csv"
MAX_STUDENT_POINTS = 100


# TODO: Review code
# TODO: Comment code


@click.command()
@click.argument('prefix')
def main(prefix):
    current_path = pathlib.Path('.')

    students_directory = f"{prefix}_submissions"
    solutions_module = f"{prefix}_solutions"

    classlist_df = pd.read_csv(CLASSLIST_CSV_FILENAME)

    for file in current_path.glob(f"{students_directory}/{prefix}_*[a-z0-9]_Student[A-Z].py"):
        student_id, student_type = student_info_from_filename(file)

        if not f"#{student_id}" in classlist_df['Username'].values:
            print("Unrecognized student ID: " + student_id + " is not found in the classlist and will not be graded.")
            continue

        test_file = f"{prefix}_test_{student_type}"

        with open(f"{students_directory}/{file.stem}-out.txt", "w") as f:
            sys.stdout = f
            execute_tests(file.stem, test_file, students_directory, solutions_module)

    submissions_df_graded = process_outputs(students_directory, prefix, classlist_df)
    brightspace_df_with_grades_col = build_grades_csv_for_brightspace(prefix, submissions_df_graded)
    build_mail_merge_csv(prefix, brightspace_df_with_grades_col)


def execute_tests(stem, test_file, directory, solutions_module):
    print(f"Running tests on file {stem}.py....")

    module = importlib.import_module(f".{stem}", directory)
    with mock.patch(f"{test_file}.solutions_module") as mock_solutions:
        mock_solutions.return_value = importlib.import_module(solutions_module, ".")
        with mock.patch(f"{test_file}.assignment_module") as mocked:
            mocked.return_value = module
            pytest.main([__file__, f"{test_file}.py", "-vvl"])


def process_outputs(students_directory, prefix, submissions_df):

    submissions_df.insert(3, 'Grade', 0)
    submissions_df['Grade'] = 0

    current_path = pathlib.Path('.')
    for file in current_path.glob(f"{students_directory}/{prefix}_*-out.txt"):
        student_id, student_type = student_info_from_filename(file)
        with open(file) as f:
            data = f.read().splitlines()

        regex = re.compile(r'\S+_GRADE([\d]+)(\[.+])? (PASSED|FAILED)')

        total_grade = 0
        current_grade = 0

        for line in data:
            m = regex.search(line)
            if m:
                total_grade += int(m.group(1))
                current_grade += int(m.group(1)) if m.group(3) == "PASSED" else 0

        submissions_df.loc[submissions_df.Username == f"#{student_id}", 'Grade'] = round(current_grade/total_grade*MAX_STUDENT_POINTS)

        submission_file = f"{students_directory}/{prefix}_{student_id}_{student_type}.py"
        with open(submission_file) as f:
            content = f.read()

        sys.stdout = open(submission_file, "w")
        print("'''")
        print("Hello, this is your autograder score, see below.")
        print(f"Score: {current_grade}/{total_grade}")
        print("'''")
        print("\n")
        print(content)

    sys.stdout = sys.__stdout__

    return submissions_df


def build_grades_csv_for_brightspace(prefix, submissions_df_graded):
    grades_csv_filename = f"{prefix}_grades.csv"
    grade_header = "Mini-Milestone {} - Objective Points Grade <Numeric MaxPoints:{}>" \
        .format(prefix, MAX_STUDENT_POINTS)

    brightspace_upload_df = submissions_df_graded

    brightspace_df_with_grades_col = brightspace_upload_df.copy()
    brightspace_upload_df.rename(columns={"Grade": grade_header}, inplace=True)

    brightspace_upload_df.to_csv(grades_csv_filename, index=False)

    return brightspace_df_with_grades_col


def build_mail_merge_csv(prefix, classlist_graded_df):
    mail_merge_csv_filename = f"{prefix}_mail_merge.csv"

    del classlist_graded_df["End-of-Line Indicator"]
    classlist_graded_df['Username'] = classlist_graded_df['Username'].apply(lambda x: x.lstrip("#"))
    classlist_graded_df['Grade'] = classlist_graded_df['Grade'].apply(lambda x: f"{x}/{MAX_STUDENT_POINTS}")
    classlist_graded_df.insert(1, 'Email', classlist_graded_df["Username"] + "@mcmaster.ca")
    classlist_graded_df.to_csv(mail_merge_csv_filename, index=False)


def student_info_from_filename(filename):
    filename_regex = re.compile(r'.*_([\d\w]*)_([\w]*)')
    student_id = re.match(filename_regex, filename.stem).group(1)
    student_type = re.match(filename_regex, filename.stem).group(2)
    return student_id, student_type


if __name__ == "__main__":
    main()
