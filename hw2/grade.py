"""
Instructor script for autograding portions of EAS 5850 HW 2 (Summer 2024).

Author(s):
    Michael Yao @michael-s-yao

Licensed under the MIT License. Copyright University of Pennsylvania 2024.
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union


# Correct answer to parts (3) and (4) of HW 2.
CORRECT_ANSWER = {
    "Age": None,
    "Sex": "F",
    "StudyDescription": "CT ABD PELVIS(WITH CHEST IMAGES) W IV CON",
    "Modality": "CT",
    "Manufacturer": "TOSHIBA",
    "PatientID": "A034518",
    "NumSeries": 1,
    "StudyInstanceUID": (
        "1.3.6.1.4.1.14519.5.2.1.99.1071.28052166218470275068707230421869"
    ),
    "num_rows": 512,
    "num_cols": 512,
    "min_pixel_value": -2048,
    "max_pixel_value": 1863,
    "mean_pixel_value": -929
}


def grade(
    study_info: Dict[str, Any],
    key: str,
    reference_correct_answer: Dict[str, Any],
    case_sensitive: bool = False
) -> int:
    """
    Grades whether the value in a given JSON study info file agrees with the
    value in a reference answer.
    Input:
        study_info: a student-generated JSON file to grade.
        key: the key in the dictionary to grade.
        reference_correct_answer: an instructor-generated JSON file that
            provides the correct answers.
        case_sensitive: whether the grader should be case sensitive in
            assessing if a student answer is correct. Default False.
    Returns:
        One of the following integer exit codes:
            0: correct answer.
            1: incorrect answer.
            2: only student answer does not contain the input key.
            3: only instructor answer does not contain the input key.
            4: both student and instructor answer does not contain the input
                key.
    """
    if key not in study_info.keys() and (
        key not in reference_correct_answer.keys()
    ):
        return 4
    elif key not in reference_correct_answer.keys():
        return 3
    elif key not in study_info.keys():
        return 2
    student_answer = str(study_info[key])
    correct_answer = str(reference_correct_answer[key])
    if not case_sensitive:
        student_answer = student_answer.lower()
        correct_answer = correct_answer.lower()
    return 1 - int(student_answer == correct_answer)


def read(
    student_answer_path: Union[Path, str]
) -> Optional[Dict[str, Any]]:
    """
    Reads a student's answer output JSON file.
    Input:
        student_answer_path: file path to the student's answer file.
    Returns:
        The student's answers as a JSON object. If the specified path is not
        a valid JSON file, then None is returned.
    """
    with open(student_answer_path, "r") as f:
        student_answer = json.load(f)
    try:
        with open(student_answer_path, "r") as f:
            student_answer = json.load(f)
    except ValueError:
        return None
    return student_answer


def build_args() -> argparse.Namespace:
    """
    Builds the arguments required to run the main grading script.
    Input:
        None.
    Returns:
        A namespace containing the argument values.
    """
    parser = argparse.ArgumentParser(description="EAS 5850 HW 2 Grader")
    parser.add_argument(
        "-a",
        "--student-answer-path",
        type=str,
        required=True,
        help="Path to the student JSON file output."
    )
    return parser.parse_args()


def main(student_answer_path: Union[Path, str]) -> int:
    # Read in the student's answer.
    student_answers = read(student_answer_path)
    if student_answers is None:
        logging.debug(f"{student_answer_path} is not a valid JSON file.")
        return 0

    # Grade the student's responses:
    num_points = 0
    for key in CORRECT_ANSWER.keys():
        exit_code = grade(
            student_answers, key, CORRECT_ANSWER, case_sensitive=False
        )
        if exit_code == 0:
            num_points += 1
        else:
            logging.debug(f"Error code {exit_code} on grading {key}")
    return num_points


if __name__ == "__main__":
    args = build_args()
    student_answer_path = args.student_answer_path
    score = main(student_answer_path)
    print(score)
