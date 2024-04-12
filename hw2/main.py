"""
Instructor implementation for EAS 5850 HW 2 (Summer 2024).

Author(s):
    Michael Yao @michael-s-yao

Licensed under the MIT License. Copyright University of Pennsylvania 2024.
"""
import json
import logging
import pyorthanc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union


# Student Penn ID.
PENN_ID: int = 12345678


# Path to save the retrieved study info to.
SAVEPATH: Union[Path, str] = "study_info.json"


class StudyInfo(NamedTuple):
    Age: Optional[int]
    Sex: str
    StudyDescription: str
    Modality: str
    Manufacturer: str
    PatientID: str
    NumSeries: int
    StudyInstanceUID: str


def get_study_info(
    client: pyorthanc.Orthanc, patient_id: str
) -> Tuple[
    Optional[StudyInfo],
    Optional[pyorthanc.Patient],
    Optional[pyorthanc.Study],
    Optional[pyorthanc.Series]
]:
    """
    Retrieves the information about a patient study.
    Input:
        client: an Orthanc client to retrieve the study info from.
        patient_id: the patient ID to query by.
    Returns:
        study_info: a StudyInfo object. Returns None if no patient was found.
        patient: a Patient object. Returns None if no patient was found.
        study: a Study object. Returns None if no patient was found.
        series: a Series object. Returns None if no patient was found.
    """
    query_results = pyorthanc.find_patients(client, {"PatientID": patient_id})
    if len(query_results) == 0:
        return None, None, None, None
    patient = next(iter(query_results))

    patient_info = patient.get_main_information()["MainDicomTags"]
    bday, age = patient.birth_date, None
    DAYS_PER_YEAR = 365.25
    if bday is not None:
        age = int((datetime.now() - bday).days / DAYS_PER_YEAR)
    study = next(iter(patient.studies))
    study_info = study.get_main_information()["MainDicomTags"]
    series = next(iter(study.series))
    series_info = series.get_main_information()["MainDicomTags"]

    study_info = StudyInfo(**{
        "Age": age,
        "Sex": patient.sex,
        "StudyDescription": study_info["StudyDescription"],
        "Modality": series_info["Modality"],
        "Manufacturer": series_info["Manufacturer"],
        "PatientID": patient_info["PatientID"],
        "NumSeries": len(study.series),
        "StudyInstanceUID": study_info["StudyInstanceUID"]
    })
    return study_info, patient, study, series


def save_study_info(
    study_info: Dict[str, Any], savepath: Union[Path, str], indent: int = 2
) -> None:
    """
    Saves information about a patient study to a specified JSON filepath.
    Input:
        study_info: a dictionary of information to save.
        savepath: file path to save the study info to.
        indent: number of spaces to use for indentation. Default 2.
    Returns:
        None.
    """
    with open(savepath, "w") as f:
        json.dump(study_info, f, indent=indent)
    logging.info(f"Saved study info to {savepath}")
    return


def modify_study_info(
    patient: Optional[pyorthanc.Patient] = None,
    study: Optional[pyorthanc.Study] = None,
    series: Optional[pyorthanc.Series] = None,
    patient_replace: Dict[str, Any] = {},
    study_replace: Dict[str, Any] = {},
    series_replace: Dict[str, Any] = {},
    **kwargs
) -> None:
    """
    Modifies existing fields and sends the modified study back to the
    Orthanc server.
    Input:
        patient: a Patient object.
        study: a Study object.
        series: a Series object.
        patient_replace: the patient fields and new value to replace.
        study_replace: the study fields and new value to replace.
        series_replace: the series fields and new value to replace.
    Returns:
        None.
    """
    if series is not None and len(series_replace.keys()):
        series.modify_as_job(replace=series_replace, **kwargs)
    if study is not None and len(study_replace.keys()):
        study.modify_as_job(replace=study_replace, **kwargs)
    if patient is not None and len(patient_replace.keys()):
        patient.modify_as_job(replace=patient_replace, **kwargs)
    return


def main(
    penn_id: int,
    patient_id: str = "A034518",
    orthanc_url: Union[Path, str] = "http://localhost:8042",
    username: str = "orthanc",
    password: str = "orthanc",
    instance_idx: int = 0,
    savepath: Optional[Union[Path, str]] = None,
    **kwargs
):
    assert 10000000 <= penn_id <= 99999999, "Must provide valid Penn ID"

    client = pyorthanc.Orthanc(
        orthanc_url,
        username=username,
        password=password
    )

    # Retrieve the requested information about the existing study.
    study_info, patient, study, series = get_study_info(client, patient_id)
    assert study_info is not None, "Patient {patient_id} query failed"

    # Answer the questions about the imaging study.
    image = series.instances[instance_idx].get_pydicom().pixel_array
    num_rows, num_cols = image.shape
    min_pixel_val, max_pixel_val = image.min(), image.max()
    mean_pixel_val = image.mean()
    logging.info(f"Number of Rows: {num_rows}")
    logging.info(f"Number of Columns: {num_cols}")
    logging.info(f"Minimum Pixel Value: {min_pixel_val}")
    logging.info(f"Maximum Pixel Value: {max_pixel_val}")
    logging.info(f"Average Pixel Value: {mean_pixel_val}")

    if savepath is not None:
        save_data = study_info._asdict()
        save_data.update(
            num_rows=int(num_rows),
            num_cols=int(num_cols),
            min_pixel_value=int(min_pixel_val),
            max_pixel_value=int(max_pixel_val),
            mean_pixel_value=int(mean_pixel_val),
        )
        save_study_info(save_data, savepath, **kwargs)

    # Modify the study.
    new_instance_uid = study_info.StudyInstanceUID[:len(str(penn_id))] + (
        str(penn_id)
    )
    modify_study_info(
        patient=patient,
        study=study,
        series=series,
        patient_replace={"PatientSex": "O", "PatientID": "8675309"},
        study_replace={
            "AccessionNumber": f"EAS5850-{penn_id}",
            "StudyInstanceUID": new_instance_uid,
            "StudyDate": "20221231",
            "ReferringPhysicianName": "Doctor^Spock"
        },
        series_replace={},
        force=True,
        keep_source=False
    )
    logging.info("Done!")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    main(PENN_ID, savepath=SAVEPATH)
