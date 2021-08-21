import importlib
import pathlib
import unittest.mock as mock
import pytest
import sys
import click
import re
import pandas as pd

CLASSLIST_CSV_FILENAME = "Classlist.csv"

# TODO: Update the grades list and mail merge CSV to include names of those whose submissions were not graded
# TODO: Review code
# TODO: Comment code


@click.command()
@click.option('--student-dir', '-s', 'students_directory', default=None)
@click.option('--solutions', 'solutions_module', default=None)
@click.argument('prefix')
def runtest(prefix, students_directory, solutions_module):
    current_path = pathlib.Path('.')

    if students_directory is None:
        students_directory = f"{prefix}_submissions"
    if solutions_module is None:
        solutions_module = f"{prefix}_solutions"

    submissions_df = pd.DataFrame(columns=['Username'])

    for file in current_path.glob(f"{students_directory}/{prefix}_*[a-z0-9]_Student[A-Z].py"):
        student_id, student_type = student_info_from_filename(file)
        test_file = f"{prefix}_test_{student_type}"
        submissions_df = submissions_df.append({'Username': student_id}, ignore_index=True)

        with open(f"{students_directory}/{file.stem}-out.txt", "w") as f:
            sys.stdout = f
            execute_tests(file.stem, test_file, students_directory, solutions_module)

    total_grade, submissions_df_graded = process_outputs(students_directory, prefix, submissions_df)
    brightspace_df_with_grades_col = build_grades_csv_for_brightspace(prefix, total_grade, submissions_df_graded)
    build_mail_merge_csv(prefix, total_grade, brightspace_df_with_grades_col)


def execute_tests(stem, test_file, directory, solutions_module):
    print(f"Running tests on file {stem}.py....")

    module = importlib.import_module(f".{stem}", directory)
    with mock.patch(f"{test_file}.solutions_module") as mock_solutions:
        mock_solutions.return_value = importlib.import_module(solutions_module, ".")
        with mock.patch(f"{test_file}.assignment_module") as mocked:
            mocked.return_value = module
            pytest.main([__file__, f"{test_file}.py", "-vvl"])


def process_outputs(students_directory, prefix, submissions_df):
    # TODO: Deal with different grade maximums for different student types

    total_grade = 0
    submissions_df['Grade'] = ''

    current_path = pathlib.Path('.')
    for file in current_path.glob(f"{students_directory}/{prefix}_*-out.txt"):
        student_id, student_type = student_info_from_filename(file)
        with open(file) as f:
            data = f.read().splitlines()

        regex = re.compile(r'\S+_GRADE([\d]+)(\[.+])? (PASSED|FAILED)')

        current_grade = 0

        if not total_grade:
            #  If total grade has not been calculated yet
            for line in data:
                m = regex.search(line)
                if m:
                    total_grade += int(m.group(1))

        for line in data:
            m = regex.search(line)
            if m:
                current_grade += int(m.group(1)) if m.group(3) == "PASSED" else 0

        submissions_df.loc[submissions_df.Username == student_id, 'Grade'] = current_grade

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

    return total_grade, submissions_df


def build_grades_csv_for_brightspace(prefix, max_student_points, submissions_df_graded):
    grades_csv_filename = f"{prefix}_grades.csv"
    grade_header = "Mini-Milestone {} - Objective Points Grade <Numeric MaxPoints:{}>" \
        .format(prefix, max_student_points)

    brightspace_upload_df = submissions_df_graded

    # Brightspace requirements, add # symbol to beginning of first column and add an EOL indicator column
    brightspace_upload_df['Username'] = brightspace_upload_df['Username'].apply(lambda x: "#" + x)
    brightspace_upload_df["End-of-Line Indicator"] = "#"

    brightspace_df_with_grades_col = brightspace_upload_df.copy()
    brightspace_upload_df.rename(columns={"Grade": grade_header}, inplace=True)

    brightspace_upload_df.to_csv(grades_csv_filename, index=False)

    return brightspace_df_with_grades_col


def build_mail_merge_csv(prefix, max_student_points, brightspace_df_with_grades_col):
    mail_merge_csv_filename = f"{prefix}_mail_merge.csv"
    classlist_df = pd.read_csv(CLASSLIST_CSV_FILENAME)

    mail_merge_df = pd.merge(classlist_df, brightspace_df_with_grades_col, on=["Username", "End-of-Line Indicator"])
    del mail_merge_df["End-of-Line Indicator"]
    mail_merge_df['Username'] = mail_merge_df['Username'].apply(lambda x: x.lstrip("#"))
    mail_merge_df['Grade'] = mail_merge_df['Grade'].apply(lambda x: f"{x}/{max_student_points}")
    mail_merge_df.insert(1, 'Email', mail_merge_df["Username"] + "@mcmaster.ca")
    mail_merge_df.to_csv(mail_merge_csv_filename, index=False)


def student_info_from_filename(filename):
    filename_regex = re.compile(r'.*_([\d\w]*)_([\w]*)')
    student_id = re.match(filename_regex, filename.stem).group(1)
    student_type = re.match(filename_regex, filename.stem).group(2)
    return student_id, student_type


if __name__ == "__main__":
    runtest()
