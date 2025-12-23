import numpy as np

from pandas import DataFrame
from geopy.distance import geodesic, great_circle

from extractor import NMEA_Columns, sort_by_time_df

knts_to_mps = lambda spd_knts: spd_knts * 0.514444
knts_to_mph = lambda spd_knts: knts_to_mps(spd_knts) * 2.23694
km_to_mi = lambda dist_km: dist_km / 1.609344
mi_to_km = lambda dist_mi: dist_mi * 1.609344


def calculate_average_moving_speed_knts(
    nmea_data: DataFrame, speed_threshold: float = 0
) -> float:
    return nmea_data.loc[
        nmea_data[NMEA_Columns.KN_GND_SPEED] > speed_threshold,
        NMEA_Columns.KN_GND_SPEED,
    ].mean()


_extract_points = lambda nmea_data, i: (
    nmea_data.loc[i, NMEA_Columns.LATITUDE],
    nmea_data.loc[i, NMEA_Columns.LONGITUDE],
)
_coord_dist_function = lambda nmea_data, prev_idx, cur_idx, func: func(
    _extract_points(nmea_data, prev_idx), _extract_points(nmea_data, cur_idx)
)


def _calc_dist_by_formula(nmea_data: DataFrame, pt_to_pt_dist_function) -> float:
    total_distance = 0
    time_sorted = sort_by_time_df(nmea_data)

    for i in range(1, len(time_sorted)):
        total_distance += pt_to_pt_dist_function(time_sorted, i - 1, i)

    return total_distance


def calculate_distance_traveled_geodesic_km(nmea_data: DataFrame) -> float:
    return _calc_dist_by_formula(
        nmea_data,
        lambda nmea_data, prev_idx, cur_idx: _coord_dist_function(
            nmea_data, prev_idx, cur_idx, geodesic
        ).kilometers,
    )


def calculate_distance_traveled_haversine_km(nmea_data: DataFrame) -> float:
    return _calc_dist_by_formula(
        nmea_data,
        lambda nmea_data, prev_idx, cur_idx: _coord_dist_function(
            nmea_data, prev_idx, cur_idx, great_circle
        ).kilometers,
    )


_get_time_delta = lambda nmea_data, prev_idx, cur_idx: (
    nmea_data.loc[cur_idx, NMEA_Columns.TIMESTAMP]
    - nmea_data.loc[prev_idx, NMEA_Columns.TIMESTAMP]
).total_seconds()


def calculate_distance_traveled_speed(
    nmea_data: DataFrame, speed_threshold: float = 0
) -> float:
    def step_integration(nmea_data: DataFrame, prev_idx: int, cur_idx: int):
        velocity: float = nmea_data.loc[prev_idx, NMEA_Columns.MPS_GND_SPEED]
        return (
            _get_time_delta(nmea_data, prev_idx, cur_idx) * velocity / 1000
            if velocity > speed_threshold
            else 0
        )

    return _calc_dist_by_formula(nmea_data, step_integration)
