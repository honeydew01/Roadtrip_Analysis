from pprint import pprint

import numpy as np
from numpy import ndarray
from pynmea2 import parse, NMEASentence, ParseError
from pathlib import Path
from datetime import datetime, timezone
from pandas import DataFrame

time_lambda = lambda nmea: datetime.strptime(
    f"{nmea.datestamp.strftime("%Y-%m-%d")} {nmea.timestamp.strftime("%H:%M:%S.%f")}",
    "%Y-%m-%d %H:%M:%S.%f",
).replace(tzinfo=timezone.utc)

speed_mps_lambda = lambda nmea: nmea.spd_over_grnd * 0.514444
speed_miph_lambda = lambda nmea: speed_mps_lambda(nmea) * 2.23694


class NMEA_Columns:
    TIMESTAMP = "Timestamp"
    LONGITUDE = "Longitude"
    LATITUDE = "Latitude"
    KN_GND_SPEED = "Ground Speed"
    TRUE_COURSE = "True Course"
    MAG_VAR = "Magnetic Variation"
    MAG_VAR_DIR = "Magnetic Variation Direction"
    MODE_INDICATOR = "Mode Indicator"
    NAV_STAT = "Navigational Status"
    MiPH_GND_SPEED = "Ground Speed (mph)"
    MPS_GND_SPEED = "Ground Speed (mps)"


def extract_file_paths(dir: Path) -> list[Path]:
    assert isinstance(dir, Path)
    files: list[Path] = []
    for thing in dir.iterdir():
        if thing.is_file():
            files.append(thing)
    return files


def extract_NMEA(file: Path) -> list[NMEASentence]:
    assert isinstance(file, Path)
    sentences = []
    with open(file, "r") as f:
        for line in f:
            try:
                msg = parse(line)
                if (
                    msg.identifier() == "GPRMC,"
                ):  # Only catch if the sentence is GPRMC for my case
                    if (
                        msg.data[2] == "V"
                    ):  # If pos_status field is 'V', position data is invalid so skip.
                        continue

                    if (
                        msg.mode_indicator == "N"
                    ):  # If mode_indicator field is N, data is not valid
                        continue

                    sentences.append(msg)
                else:
                    raise TypeError("Don't know how to deal with GPRMC sentences")

            except ParseError as e:
                print("Parse error: {}".format(e))
                continue
    return sentences


def extract_NMEAs(files: list[Path]) -> list[NMEASentence]:
    items = []
    for file in files:
        items += extract_NMEA(file)
    return items


def extract_NMEAs_df(files: list[Path]) -> DataFrame:
    nmeas = extract_NMEAs(files)

    entries: list[dict] = []

    for nmea in nmeas:
        entries.append(
            {
                NMEA_Columns.TIMESTAMP: time_lambda(nmea),
                NMEA_Columns.LONGITUDE: nmea.longitude,
                NMEA_Columns.LATITUDE: nmea.latitude,
                NMEA_Columns.KN_GND_SPEED: nmea.spd_over_grnd,
                NMEA_Columns.MPS_GND_SPEED: speed_mps_lambda(nmea),
                NMEA_Columns.MiPH_GND_SPEED: speed_miph_lambda(nmea),
                NMEA_Columns.TRUE_COURSE: nmea.true_course,
                NMEA_Columns.MAG_VAR: nmea.mag_variation,
                NMEA_Columns.MAG_VAR_DIR: nmea.mag_var_dir,
                NMEA_Columns.MODE_INDICATOR: nmea.mode_indicator,
                NMEA_Columns.NAV_STAT: nmea.nav_status,
            }
        )

    return DataFrame(entries)


def sort_by_time_df(nmea_data: DataFrame) -> DataFrame:
    return nmea_data.sort_values(by=NMEA_Columns.TIMESTAMP).reset_index(drop=True)


# def get_idle_intervals(nmea_data: DataFrame, threshold : float = 0, miph_threshold: float = 0, mps_threshold : float = 0) -> list[int]:
#     threshold_unit = NMEA_Columns.MPS_GND_SPEED if mps_threshold != 0 else NMEA_Columns.KN_GND_SPEED
#     threshold_unit = NMEA_Columns.MiPH_GND_SPEED if miph_threshold != 0 else NMEA_Columns.KN_GND_SPEED

#     result = []
#     for i in range(len(nmea_data)):
#         if nmea_data.loc[i, threshold_unit] <= threshold:
#             result.append(i)

#     idle_indices = np.array(get_still_indices(sorted_nmea_tx_to_md, miph_threshold=0.5))
#     idle_intervals = []
#     running = False
#     prev_idx = 0
#     current_run_start_idx = 0
#     for idle_idx in idle_indices:
#         if not running:
#             current_run_start_idx = idle_idx
#             running = True
#             prev_idx = idle_idx
#             continue

#         if prev_idx != idle_idx - 1:
#             running = False
#             idle_intervals.append((current_run_start_idx, prev_idx))

#         prev_idx = idle_idx


def get_data_breaks(nmea_data: DataFrame) -> list[int]:
    deltas = []

    prev_time = None
    for i in range(0, len(nmea_data)):
        if prev_time is None:
            prev_time = nmea_data.loc[i, NMEA_Columns.TIMESTAMP]
            continue

        cur_time = nmea_data.loc[i, NMEA_Columns.TIMESTAMP]
        delta = cur_time - prev_time
        deltas.append(delta.total_seconds())
        if delta.total_seconds() < 0:
            raise ValueError(
                f"At index {i}, the previous row in the dataframe had a timestamp later than this."
                f"\n\tPrevious Timestamp: {prev_time.strftime("%Y-%m-%d %H:%M:%S.%f")} "
                f"\n\tThis Timestamp: {cur_time.strftime("%Y-%m-%d %H:%M:%S.%f")}"
            )

        prev_time = cur_time

    deltas = np.array(deltas)
    mean = np.mean(deltas)
    std = np.std(deltas, ddof=1)

    deltas_z_scores = np.abs((deltas - mean) / std)
    return np.where(np.abs(deltas_z_scores) > 1)[0]
