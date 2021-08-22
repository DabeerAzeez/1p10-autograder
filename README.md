# 1P10 Autograder User Guide

## Step 1: Setup

Ensure the following items are setup properly

- A class list `.csv` file downloaded from your Brightspace Learning Management System (e.g., Avenue to Learn)

- A `/MMXX_submissions` folder containing all student submissions
  - Student submissions are expected to be of the form `MMXX_studentID_Student?.py` 
    - For example, `MM04_abdulazd_StudentA.py` or `MM05_awani3.py`
    - Where `XX` is a two digit number
    - Where `?` represents a letter from A to Z
    - Where `_Student?` (e.g., `_StudentA`) refers to a "student type;" an optional identifier that can be used to differentiate between different types of students who have different assigned questions for an assignment
- A `MMXX_solutions.py` solutions file for the methods being tested in assignment `MMXX`
  - Contains solutions for all methods in assignment `MMXX` across student types
- A `MMXX_test_Student?.py` Pytest test file containing boilerplate code for the test harness as well as PyTest tests for testing the functions seen in `MMXX_solutions.py`
  - All student types found in the submissions folder must have respective test files present
  - Boilerplate code is provided below:

```python

import pytest
import unittest.mock as mock


# BOILER PLATE -- NEEDED BY THE TEST HARNESS
def assignment_module():
    pass


def solutions_module():
    pass


@pytest.fixture
def module():
    return assignment_module()


@pytest.fixture
def solutions():
    return solutions_module()
# END BOILER PLATE CODE


# Mocking print and input as fixtures since they're used often
@pytest.fixture
def mock_print():
    with mock.patch("builtins.print") as mock_print:
        yield mock_print


@pytest.fixture
def mock_input():
    with mock.patch("builtins.input") as mock_input:
        yield mock_input


#  INSERT PYTEST TESTS BELOW
```

## Step 2: Running the Autograder

- Open your command line within the directory containing `_main.py` and run the following command:
  - `python _main.py <prefix>`
    - Where `<prefix>` refers to the "prefix" of the assignment (e.g., `MM04`)

## Behaviour

The Autograder will:

1. Create output text files for each student submission within the submission directory
2. Create a `<prefix>_grades.csv` file, calculating the grades for all students in the class list csv, assigning a grade of zero to those who did not submit files or did not submit files that were properly recognized by the autograder
3. Create a `<prefix>_mail_merge.csv` file which can be used to send a mail merge email to all students (emails are generated from based on their Brightspace username) 
   1. Includes each student's grade for the assignment `<prefix>` as a fraction 
