"""
Instructor implementation for EAS 5850 HW 2 (Summer 2024).

Author(s):
    Michael Yao @michael-s-yao

Licensed under the MIT License. Copyright University of Pennsylvania 2024.
"""
import json
import logging
import pyorthanc
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union


# Student Penn ID.
PENN_ID: int = 12345678


# Path to save the retrieved study info to.
SAVEPATH: Union[Path, str] = "study_info.json"


class InstanceInfo(NamedTuple):
    Age: str
    Sex: str
    StudyDescription: str
    Modality: str
    Manufacturer: str
    PatientID: str
    NumSeries: int
    StudyInstanceUID: str
    NumRows: int
    NumCols: int
    MinPixelVal: float
    MaxPixelVal: float
    MeanPixelVal: float


def get_instance_info(
    client: pyorthanc.Orthanc,
    patient_id: str,
    series_number: int,
    instance_number: int
) -> Tuple[
    Optional[InstanceInfo],
    Optional[pyorthanc.Patient],
    Optional[pyorthanc.Study],
    Optional[pyorthanc.Series],
    Optional[pyorthanc.Instance],
]:
    """
    Retrieves the information about a patient study.
    Input:
        client: an Orthanc client to retrieve the study info from.
        patient_id: the patient ID to query by.
        series_number: the index of the series in the study to retrieve.
        instance_number: the index of the isntance in the series to retreive.
    Returns:
        instance_info: an InstanceInfo object. Returns None if no patient was
            found.
        patient: a Patient object. Returns None if no patient was found.
        study: a Study object. Returns None if no patient was found.
        series: a Series object. Returns None if no patient was found.
        instance: an Instance object. Returns None if no patient was found.
    """
    query_results = pyorthanc.find_patients(client, {"PatientID": patient_id})
    if len(query_results) == 0:
        return None, None, None, None

    patient = next(iter(query_results))
    patient_info = patient.main_dicom_tags

    study = next(iter(patient.studies))
    study_info = study.main_dicom_tags

    series = next(
        filter(lambda x: x.series_number == series_number, study.series)
    )
    series_info = series.main_dicom_tags

    instance = next(
        filter(
            lambda x: x.instance_number == instance_number, series.instances
        )
    )

    image_data = instance.get_pydicom().pixel_array
    num_rows, num_cols = image_data.shape
    min_pixel_val, max_pixel_val = image_data.min(), image_data.max()
    mean_pixel_val = image_data.mean()

    instance_info = InstanceInfo(**{
        "Age": instance.tags["0010,1010"]["Value"],
        "Sex": patient.sex,
        "StudyDescription": study_info["StudyDescription"],
        "Modality": series_info["Modality"],
        "Manufacturer": series_info["Manufacturer"],
        "PatientID": patient_info["PatientID"],
        "NumSeries": len(study.series),
        "StudyInstanceUID": study_info["StudyInstanceUID"],
        "NumRows": int(num_rows),
        "NumCols": int(num_cols),
        "MinPixelVal": float(min_pixel_val),
        "MaxPixelVal": float(max_pixel_val),
        "MeanPixelVal": float(mean_pixel_val),
    })
    return instance_info, patient, study, series, instance


def save_instance_info(
    instance_info: Dict[str, Any], savepath: Union[Path, str], indent: int = 2
) -> None:
    """
    Saves information about a patient instance to a specified JSON filepath.
    Input:
        instance_info: a dictionary of information to save.
        savepath: file path to save the study info to.
        indent: number of spaces to use for indentation. Default 2.
    Returns:
        None.
    """
    with open(savepath, "w") as f:
        json.dump(instance_info, f, indent=indent)
    logging.info(f"Saved instance info to {savepath}")
    return


def modify_instance_info(
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
    series_number: int = 4,
    instance_number: int = 130,
    savepath: Optional[Union[Path, str]] = None,
    **kwargs
):
    assert 10000000 <= penn_id <= 99999999, "Must provide valid Penn ID"

    client = pyorthanc.Orthanc(
        orthanc_url,
        username=username,
        password=password
    )

    # Retrieve the requested information about the existing study, and
    # answer the questions about the imaging study.
    instance_info, patient, study, series, _ = get_instance_info(
        client,
        patient_id,
        series_number=series_number,
        instance_number=instance_number
    )
    assert instance_info is not None, "Patient {patient_id} query failed"

    if savepath is not None:
        save_instance_info(instance_info._asdict(), savepath, **kwargs)

    # Modify the study.
    new_instance_uid = instance_info.StudyInstanceUID[:len(str(penn_id))] + (
        str(penn_id)
    )
    modify_instance_info(
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
