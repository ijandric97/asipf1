import os
import warnings

import ergast
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from constants import IMAGES_DPI, IMAGES_PITSTOPS_FOLDER, IMAGES_SIZE, PITSTOPS_CSV
from utils import get_local_minimum

sns.set_theme(style="whitegrid")


def generate_dataset() -> pd.DataFrame:
    results = pd.DataFrame([])

    max_season = ergast.season_list()["year"].max()
    # Lap Time data is available from 96
    for year in range(1994, max_season + 1):
        print(f"Parsing year {year}:")
        # Get number of races in a given season
        race_count = len(ergast.race_schedule(year=year).index)

        for race in range(1, race_count + 1):  # Rounds are 1-index based
            results = pd.concat([results, get_pitstop_data(year, race)])

    results.reset_index(inplace=True, drop=True)
    results.to_csv(PITSTOPS_CSV)
    print(results)
    return results


def get_pitstop_data(year: int, race: int, degree: int = 3) -> pd.DataFrame:
    # Get race results for lets say first round 2022
    results = ergast.race_results(year=year, race=race).dropna(subset=["timeMillis"])[
        [
            "year",
            "circuitId",
            "driverId",
            "timeMillis",
            "laps",
            "position",
            "fastestLapTime",
        ]
    ]
    stops = ergast.pit_stops(year, race, pitstop=1)[
        [
            "year",
            "time",
            "circuitId",
            "driverId",
            "lap",
            "localTime",
            "pitstopDuration",
            "durationMilliseconds",
        ]
    ]
    if results.empty or stops.empty:
        print(f"SKIPPING {year} - {race} {len(results)} {len(stops)}")
        return  # Exit because no results are available

    results["fastestLap"] = (
        pd.to_datetime(results["fastestLapTime"], format="%M:%S.%f")
        + pd.DateOffset(years=70)
    ).astype(np.int64) // int(1e6)

    # Merge results and stops
    results = results.merge(stops, on=["circuitId", "driverId", "year"])
    del stops  # Optimization

    # FIXME: Time is calculated from UTC, while localTime is not, in short we got no
    # local startTime
    # results["firstStopTime"] = (
    #     pd.to_datetime(results["localTime"], format="%H:%M:%S")
    #     - pd.to_datetime(results["time"], format="%H:%M:%S")
    # ).astype(np.int64) / int(1e6)

    # Cilj nam je dobit sljedece ig?
    # year, circuitId, optimalFirstStopLap
    total_laps = results["laps"].max()
    results["avgLapTime"] = results["timeMillis"] / total_laps
    circuit_id = results["circuitId"].iat[0]
    actual_x = results.loc[results["avgLapTime"].idxmin()]["lap"]

    x = results["lap"]
    y = results["avgLapTime"]

    avg_lap = results["fastestLap"].mean()
    if avg_lap < 0:
        avg_lap = y.mean()

    avg_duration = results[results["durationMilliseconds"] < avg_lap][
        "durationMilliseconds"
    ].mean()

    with warnings.catch_warnings(record=True) as w:
        min_x = actual_x
        regression_model = np.poly1d(np.polyfit(x, y, degree))
        minimums = get_local_minimum(regression_model)[0]
        if minimums.size > 0:
            local_minimum = round(minimums.min())
            if local_minimum > 1 and local_minimum < total_laps:
                min_x = local_minimum

        # if len(w) > 0:
        #     print(results)
        #     plot_regression(
        #         x, y, regression_model, min_x, f"{year} - {race} - {circuit_id}"
        #     )

    return pd.DataFrame(
        {
            "year": [year],
            "circuitId": [circuit_id],
            "optimalFirstStopLap": [min_x],
            "lap": [actual_x],
            "avgDuration": [avg_duration],
            "avgLapTime": [avg_lap],
        }
    )


# grouped = df.groupby(["circuitId"])
# for name, group in grouped:
#     print(name)
#     print(group)

#     fig, ax = plt.subplots(figsize=IMAGES_SIZE)
#     plt.title(f"{name}")
#     # ax.plot(group["year"], group["optimalFirstStopLap"], "-o")
#     # ax.axhline(group["optimalFirstStopLap"].mean(), color="r", linestyle="--")
#     # ax.plot(group["year"], group["lap"], "-o")
#     # ax.axhline(group["lap"].mean(), color="g", linestyle="--")
#     ax.plot(group["year"], group["avgDuration"], "-o")
#     plt.savefig(f"{IMAGES_PITSTOPS_FOLDER}/{name}.png", dpi=IMAGES_DPI)


def _analyze_duration(df: pd.DataFrame) -> None:
    grouped = df.groupby(["year"])
    res = pd.DataFrame()
    for name, group in grouped:
        item = pd.DataFrame(
            {
                "year": [name],
                "optimal": group["optimalFirstStopLap"].mean(),
                "avg": group["lap"].mean(),
                "avgDuration": group["avgDuration"].mean(),
            }
        )
        res = pd.concat([res, item])
    res.reset_index(inplace=True, drop=True)

    fig, ax = plt.subplots()
    plt.title("Average first pitstop duration")
    ax.plot(res["year"], res["avgDuration"], "-o")
    # ax.plot(res["year"], res["optimal"], "-o")
    # ax.axhline(res["optimal"].mean(), color="r", linestyle="--")
    # ax.plot(res["year"], res["avg"], "-o")
    # ax.axhline(res["avg"].mean(), color="g", linestyle="--")
    plt.show()


def analyze(force_generate_dataset: bool = False) -> None:
    if not os.path.exists(IMAGES_PITSTOPS_FOLDER):
        os.makedirs(IMAGES_PITSTOPS_FOLDER)

    if not os.path.exists(PITSTOPS_CSV) or force_generate_dataset:
        print("Pitstops CSV not found, generating dataset.")
        df = generate_dataset()
    else:
        df = pd.read_csv(PITSTOPS_CSV)

    _analyze_duration(df)


if __name__ == "__main__":
    analyze()
