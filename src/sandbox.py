import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from zoneinfo import ZoneInfo
from pprint import pprint

from env_vars import *
from extractor import (
    extract_file_paths,
    extract_NMEAs_df,
    NMEA_Columns,
    get_data_breaks,
)
from misc_math import sort_by_time_df


if __name__ == "__main__":
    nmeas = extract_NMEAs_df(extract_file_paths(DATA_DIR))
    nmeas_tx_to_md = nmeas.loc[
        (
            nmeas[NMEA_Columns.TIMESTAMP]
            >= datetime(2025, 12, 13, tzinfo=ZoneInfo("America/Chicago"))
        )
        & (
            nmeas[NMEA_Columns.TIMESTAMP]
            <= datetime(2025, 12, 15, tzinfo=ZoneInfo("America/New_York"))
        )
    ]
    sorted_nmea_tx_to_md = sort_by_time_df(nmeas_tx_to_md)

    breaks = get_data_breaks(sorted_nmea_tx_to_md)
    print(f"Found {len(breaks)} breaks in time data.")

    speed_data = nmeas_tx_to_md[NMEA_Columns.MiPH_GND_SPEED].to_numpy()
    time_data = nmeas_tx_to_md[NMEA_Columns.TIMESTAMP].to_numpy()
    east_time_data = np.array(
        [pt.astimezone(ZoneInfo("US/Eastern")) for pt in time_data]
    )
    fig = plt.figure(figsize=(12, 8))
    plt.scatter(east_time_data, speed_data, marker=".")

    for outlying_idx in breaks:
        x_start = sorted_nmea_tx_to_md.loc[
            outlying_idx, NMEA_Columns.TIMESTAMP
        ].astimezone(ZoneInfo("US/Eastern"))
        x_end = sorted_nmea_tx_to_md.loc[
            outlying_idx + 1, NMEA_Columns.TIMESTAMP
        ].astimezone(ZoneInfo("US/Eastern"))
        plt.axvspan(x_start, x_end, color="red", alpha=0.3)

    plt.title("Speed Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Speed (mph)")
    plt.show()
