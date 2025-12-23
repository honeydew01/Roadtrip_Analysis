import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pprint import pprint
from scipy import stats


from extractor import (
    extract_file_paths,
    extract_NMEAs_df,
    NMEA_Columns,
    sort_by_time_df,
    get_data_breaks,
)

from misc_math import (
    calculate_average_moving_speed_knts,
    calculate_distance_traveled_geodesic_km,
    calculate_distance_traveled_haversine_km,
    calculate_distance_traveled_speed,
    km_to_mi,
)

from env_vars import DATA_DIR

LONG_BREAK_THRESHOLD = 3600
TRIP_START = datetime(2025, 12, 13, 12, tzinfo=ZoneInfo("America/Chicago"))
TRIP_END = datetime(2025, 12, 15, 0, tzinfo=ZoneInfo("America/New_York"))

if __name__ == "__main__":
    nmeas = extract_NMEAs_df(extract_file_paths(DATA_DIR))
    nmeas_tx_to_md = nmeas.loc[
        (
            nmeas[NMEA_Columns.TIMESTAMP]
            >= TRIP_START
        )
        & (
            nmeas[NMEA_Columns.TIMESTAMP]
            <= TRIP_END
        )
    ]
    sorted_nmea_tx_to_md = sort_by_time_df(nmeas_tx_to_md)

    ####### Average Speed Calculation
    average_speed = calculate_average_moving_speed_knts(nmeas, 0.001)
    print(f"Average Moving Speed:\n\t{average_speed:.2f} mph")

    ####### Maximum Speed Calculations
    max_speed_pt = nmeas_tx_to_md.loc[
        nmeas_tx_to_md[NMEA_Columns.KN_GND_SPEED].idxmax()
    ]
    print(
        f"Maximum Speed:"
        f"\n\tAt:         \t{max_speed_pt[NMEA_Columns.TIMESTAMP].astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")} EST"
        f"\n\tSpeed:      \t{max_speed_pt[NMEA_Columns.MiPH_GND_SPEED]:.2f} mph"
        f"\n\tCoordinates:\t({max_speed_pt[NMEA_Columns.LATITUDE]}, {max_speed_pt[NMEA_Columns.LONGITUDE]})"
    )

    ####### Breaks Calculations
    breaks = get_data_breaks(sorted_nmea_tx_to_md)
    break_times = np.array(
        [
            (
                sorted_nmea_tx_to_md.loc[break_idx + 1, NMEA_Columns.TIMESTAMP]
                - sorted_nmea_tx_to_md.loc[break_idx, NMEA_Columns.TIMESTAMP]
            ).total_seconds()
            for break_idx in breaks
        ]
    )
    average_break_time = np.mean(break_times)

    long_break_times = break_times[break_times > LONG_BREAK_THRESHOLD]
    average_long_break_time = np.mean(long_break_times) if len(long_break_times) else 0

    short_break_times = break_times[break_times < LONG_BREAK_THRESHOLD]
    average_short_break_time = (
        np.mean(short_break_times) if len(short_break_times) else 0
    )

    print(
        f"Break Data:"
        f"\n\tTotal Number of breaks:    \t{len(breaks)}"
        f"\n\tTotal Average Break Time:  \t{(average_break_time / 60):.2f} min"
        f"\n\t\tNumber of Short Breaks:  \t{len(short_break_times)}"
        f"\n\t\tAverage Short Break Time:\t{(average_short_break_time / 60):.2f} min"
        f"\n\t\tNumber of Long Breaks:   \t{len(long_break_times)}"
        f"\n\t\tAverage Long Break Time: \t{int(average_long_break_time / 3600)} Hours {((average_long_break_time % 3600) / 60):.2f} min"
        # f"\n\tTotal Idle Sessions:       \t{len(idle_times)}"
        # f"\n\tAverage Idle Session Time: \t{(average_idle_time / 60):.2f} min"
    )

    ####### Traveled Distance Calculations
    haversine_distance = calculate_distance_traveled_haversine_km(nmeas_tx_to_md)
    geodesic_distance = calculate_distance_traveled_geodesic_km(nmeas_tx_to_md)
    integration_distance = calculate_distance_traveled_speed(nmeas_tx_to_md)
    hav_error = abs(geodesic_distance - haversine_distance) / geodesic_distance * 100
    int_error = abs(geodesic_distance - integration_distance) / geodesic_distance * 100
    print(
        f"Total Distance Traveled:"
        f"\n\tGeodesic:         \t{geodesic_distance:.2f} km ({km_to_mi(geodesic_distance):.2f} mi)"
        f"\n\tHaversine:        \t{haversine_distance:.2f} km ({km_to_mi(haversine_distance):.2f} mi)"
        f"\n\tHaversine Error:  \t{hav_error:.2f}%"
        f"\n\tIntegration:      \t{integration_distance:.2f} km ({km_to_mi(integration_distance):.2f} mi)"
        f"\n\tIntegration Error:\t{int_error:.2f}%"
    )

    ####### Sampling Investigation
    # deltas = []
    # deltas_idxs : list[int]= []
    # for i in range(1, len(sorted_nmea_tx_to_md)):
    #     time_delta: timedelta = (
    #         sorted_nmea_tx_to_md.loc[i, NMEA_Columns.TIMESTAMP]
    #         - sorted_nmea_tx_to_md.loc[i - 1, NMEA_Columns.TIMESTAMP]
    #     )
    #     deltas.append(time_delta.total_seconds())
    #     deltas_idxs.append(i-1)

    # deltas = np.array(deltas)
    # sample_interval_mean = np.mean(deltas)
    # sample_interval_median = np.median(deltas)
    # sample_interval_mode = stats.mode(deltas)
    # sample_interval_std = np.std(deltas, ddof=1)
    # sample_interval_var = np.var(deltas, ddof=1)

    # # Assumes when operating, the gps is sampling at a uniform rate
    # sample_interval_z_scores = np.abs((deltas - sample_interval_mean) / sample_interval_std)
    # sample_interval_outlier_delta_indicies = np.where(np.abs(sample_interval_z_scores) > 2)[0]
    # sorted_nmea_outlying_indicies = [deltas_idxs[index] for index in sample_interval_outlier_delta_indicies]

    # print(
    #     f"Sampling Data:"
    #     f"\n\tMean Sampling Interval:              \t{sample_interval_mean:.2f}"
    #     f"\n\tMedian Sampling Interval:            \t{sample_interval_median:.2f}"
    #     f"\n\tMode of Sampling Interval:           \t{sample_interval_mode.mode:.2f}, Count: {sample_interval_mode.count:.2f}"
    #     f"\n\tSampling Interval Standard Deviation:\t{sample_interval_std:.2f}"
    #     f"\n\tSampling Interval Variance:          \t{sample_interval_var:.2f}"
    #     f"\n\tNumber of outlying points:           \t{len(sample_interval_outlier_delta_indicies)}"
    # )

    ####### Speed Graph
    speed_data = nmeas_tx_to_md[NMEA_Columns.MiPH_GND_SPEED].to_numpy()
    time_data = nmeas_tx_to_md[NMEA_Columns.TIMESTAMP].to_numpy()
    east_time_data = np.array(
        [pt.astimezone(ZoneInfo("US/Eastern")) for pt in time_data]
    )
    fig = plt.figure(figsize=(12, 8))
    plt.scatter(east_time_data, speed_data, marker=".")

    for idx in breaks[break_times > LONG_BREAK_THRESHOLD]:
        x_start = sorted_nmea_tx_to_md.loc[idx, NMEA_Columns.TIMESTAMP].astimezone(
            ZoneInfo("US/Eastern")
        )
        x_end = sorted_nmea_tx_to_md.loc[idx + 1, NMEA_Columns.TIMESTAMP].astimezone(
            ZoneInfo("US/Eastern")
        )
        plt.axvspan(x_start, x_end, color="red", alpha=0.3)

    for idx in breaks[break_times < LONG_BREAK_THRESHOLD]:
        x_start = sorted_nmea_tx_to_md.loc[idx, NMEA_Columns.TIMESTAMP].astimezone(
            ZoneInfo("US/Eastern")
        )
        x_end = sorted_nmea_tx_to_md.loc[idx + 1, NMEA_Columns.TIMESTAMP].astimezone(
            ZoneInfo("US/Eastern")
        )
        plt.axvspan(x_start, x_end, color="orange", alpha=0.3)

    long_breaks_event_patch = mpatches.Patch(
        color="red", alpha=0.3, label="Long Breaks"
    )
    short_breaks_event_patch = mpatches.Patch(
        color="orange", alpha=0.3, label="Short Breaks"
    )

    plt.title("Speed Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Speed (mph)")
    plt.legend(handles=[long_breaks_event_patch, short_breaks_event_patch])

    plt.show()

    exit()
