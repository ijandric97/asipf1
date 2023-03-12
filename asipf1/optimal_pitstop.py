import math
import os
import warnings

import ergast
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from core.constants import IMAGES_PITSTOPS_FOLDER, PITSTOPS_CSV
from core.utils import get_local_minimum, plot_multiple_by_time, plot_regression


def generate_dataset() -> pd.DataFrame:
    results = pd.DataFrame([])

    max_season = ergast.season_list()["year"].max()

    print(f"Generating pitstop data from 2012 till {max_season}")
    # Pitstop data is available from 2012
    for year in range(2012, max_season + 1):
        print(f"Parsing year {year}:")
        # Get number of races in a given season
        race_count = len(ergast.race_schedule(year=year).index)

        for race in range(1, race_count + 1):  # Rounds are 1-index based
            results = pd.concat([results, get_pitstop_data(year, race)])

    results.reset_index(inplace=True, drop=True)  # Concat messed up index, so reset it
    results.to_csv(PITSTOPS_CSV, index=False)

    return results


def get_pitstop_data(year: int, race: int, degree: int = 3) -> pd.DataFrame:
    # Get race results for lets say first round 2022
    results = ergast.race_results(year=year, race=race)[
        [
            "year",
            "circuitId",
            "driverId",
            "timeMillis",
            "laps",
            "position",
            "positionText",
            "fastestLapTime",
        ]
    ]
    dnfs = results[results["positionText"] == "R"]  # Get all crashes
    results = results.dropna(subset=["timeMillis"])  # Now drop non-eligible ones
    if results.empty:
        print(f"SKIPPING ({year}:{race}) -> No race results")
        return  # Exit because no results are available

    stops = ergast.pit_stops(year, race)[
        [
            "year",
            "time",
            "circuitId",
            "driverId",
            "pitstop",
            "lap",
            "localTime",
            "pitstopDuration",
            "durationMilliseconds",
        ]
    ]
    if stops.empty:
        print(f"SKIPPING ({year}:{race}) -> No pitstop data")
        return  # Exit because no results are available

    # Merge results and stops and delete stops
    results = results.merge(stops, on=["circuitId", "driverId", "year"])
    del stops  # Optimization

    # Get average number of pitstops and then only keep the first pitstops
    average_number_of_pistops = results["pitstop"].mean()
    results = results[results["pitstop"] == 1]

    results["fastestLap"] = pd.to_datetime(
        results["fastestLapTime"], format="%M:%S.%f"
    ) + pd.DateOffset(years=70)
    results["fastestLap"] = results["fastestLap"].astype(np.int64) // int(1e6)

    # Cilj nam je dobit sljedece ig?
    # year, circuitId, optimalFirstStopLap
    total_laps = results["laps"].max()
    results["avgLapTime"] = results["timeMillis"] / total_laps
    circuit_id = results["circuitId"].iat[0]
    actual_x = results.loc[results["avgLapTime"].idxmin()]["lap"]

    had_dnf = len(dnfs.query(f"laps >= {actual_x - 2} and laps <= {actual_x}")) > 0

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

    # print(results)
    # plot_regression(x, y, regression_model, min_x, f"{year} - {race} - {circuit_id}")

    return pd.DataFrame(
        {
            "year": [year],
            "circuitId": [circuit_id],
            "optimalFirstPitstopLap": [min_x],
            "actualFirstPitstopLap": [actual_x],
            "averagePitstopDuration": [avg_duration],
            "averageLapTime": [avg_lap],
            "averageNumberOfPitstops": [average_number_of_pistops],
            "hadDNFBefore": [had_dnf],
        }
    )


def _analyze_per_track(df: pd.DataFrame) -> None:
    grouped = df.groupby(["circuitId"])
    for name, group in grouped:
        plot_multiple_by_time(group, IMAGES_PITSTOPS_FOLDER + f"./{name}.png")


def _analyze_averages(df: pd.DataFrame) -> None:
    grouped = df.groupby(["year"])
    res = pd.DataFrame()
    for name, group in grouped:
        item = pd.DataFrame(
            {
                "year": [name],
                "optimalFirstPitstopLap": group["optimalFirstPitstopLap"].mean(),
                "actualFirstPitstopLap": group["actualFirstPitstopLap"].mean(),
                "averageLapTime": group["averageLapTime"].mean(),
                "averagePitstopDuration": group["averagePitstopDuration"].mean(),
                "averageNumberOfPitstops": group["averageNumberOfPitstops"].mean(),
            }
        )
        res = pd.concat([res, item])
    res.reset_index(inplace=True, drop=True)

    plot_multiple_by_time(res, IMAGES_PITSTOPS_FOLDER + "./_pitstop_averages.png")


def analyze(force_generate_dataset: bool = False) -> None:
    if not os.path.exists(IMAGES_PITSTOPS_FOLDER):
        os.makedirs(IMAGES_PITSTOPS_FOLDER)

    if not os.path.exists(PITSTOPS_CSV) or force_generate_dataset:
        print("Pitstops CSV not found, generating dataset.")
        df = generate_dataset()
    else:
        df = pd.read_csv(PITSTOPS_CSV)

    _analyze_averages(df)
    _analyze_per_track(df)


if __name__ == "__main__":
    analyze()
