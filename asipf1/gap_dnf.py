import os
import textwrap

import ergast
import numpy as np
import pandas as pd
from core.constants import (
    GAPS_CSV,
    IMAGES_DNFS_FOLDER,
    IMAGES_DNFS_SIZE,
    IMAGES_DPI,
    PERCENTAGES_CSV,
    STATUS_ACCIDENTS,
    STATUS_COLLISIONS,
)
from matplotlib import pyplot as plt


def generate_dataset() -> pd.DataFrame:
    results = pd.DataFrame([])
    percentages = pd.DataFrame([])
    gaps = pd.DataFrame([])

    max_season = ergast.season_list()["year"].max()
    # status_codes = STATUS_CODES_COLLISIONS if collisions else STATUS_CODES

    print(f"Generating data from 1996 till {max_season}")
    # Lap Time data is available from 96
    for year in range(1996, max_season + 1):
        print(f"Parsing year {year}:")
        # Get number of races in a given season
        race_count = len(ergast.race_schedule(year=year).index)

        for race in range(1, race_count + 1):  # Rounds are 1-index based
            race_percentages, race_gaps = get_race_dnfs(year, race)

            percentages = pd.concat([percentages, race_percentages])
            gaps = pd.concat([gaps, race_gaps])

            # results = pd.concat([results, get_dnfs_data(year, race)])

    # Convert to int64 and summ everything without duplicates
    percentages.sort_values(by=["percentage"], inplace=True)
    percentages = percentages.astype(np.int64)
    percentages["accidents"] = percentages.groupby(["percentage"])[
        "accidents"
    ].transform("sum")
    percentages["collisions"] = percentages.groupby(["percentage"])[
        "collisions"
    ].transform("sum")
    percentages.drop_duplicates(subset=["percentage"], inplace=True)
    percentages.reset_index(inplace=True, drop=True)
    percentages.to_csv(PERCENTAGES_CSV, index=False)

    gaps.sort_values(by=["gap"], inplace=True)
    gaps = gaps.astype(np.int64)
    gaps["accidents"] = gaps.groupby(["gap"])["accidents"].transform("sum")
    gaps["collisions"] = gaps.groupby(["gap"])["collisions"].transform("sum")
    gaps.drop_duplicates(subset=["gap"], inplace=True)
    gaps["total_accidents"] = gaps["accidents"].cumsum()
    gaps["total_collisions"] = gaps["collisions"].cumsum()
    gaps.reset_index(inplace=True, drop=True)
    gaps.to_csv(GAPS_CSV, index=False)

    # FIXME
    # # Concat messed up index, so reset it
    # results.reset_index(inplace=True, drop=True)
    # results.to_csv(DNFS_CSV, index=False)

    return percentages, gaps


def get_race_dnfs(year: int, race: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    lap_times = ergast.lap_times(year, race)
    if lap_times.empty:
        print(f"SKIPPING ({year}:{race}) -> No lap_time data")
        return (
            pd.DataFrame([]),
            pd.DataFrame([]),
        )  # Skip because no lap time data is available
    lap_count = lap_times["lap"].max()

    # Add total race time thus far in milliseconds as a new column
    agg_df = pd.DataFrame(
        lap_times.groupby(["driverId", "lap"], as_index=False)["millis"].sum()
    )
    agg_df["total_millis"] = agg_df.groupby("driverId")["millis"].cumsum()
    lap_times = lap_times.merge(agg_df, on=["driverId", "lap", "millis"])
    del agg_df

    # Get DNF Laps
    race_results = ergast.race_results(year=year, race=race)
    accident_laps = (
        race_results.query(f"statusId in {STATUS_ACCIDENTS}").reset_index(drop=True)
    )["laps"].to_list()

    collision_laps = (
        race_results.query(f"statusId in {STATUS_COLLISIONS}").reset_index(drop=True)
    )["laps"].to_list()

    race_percentages = pd.DataFrame([])
    race_gaps = pd.DataFrame([])

    for lap in accident_laps:
        percentage, gap = get_lap_dnfs(year, race, lap, lap_count, lap_times)
        race_percentages = pd.concat([race_percentages, percentage])
        race_gaps = pd.concat([race_gaps, gap])
    for lap in collision_laps:
        percentage, gap = get_lap_dnfs(year, race, lap, lap_count, lap_times, True)
        race_percentages = pd.concat([race_percentages, percentage])
        race_gaps = pd.concat([race_gaps, gap])

    return race_percentages, race_gaps


def get_lap_dnfs(
    year: int,
    race: int,
    lap: int,
    lap_count: int,
    lap_times: pd.DataFrame,
    is_collision: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # We are looking at the end of completed lap, this fixes the 0 lap issue
    current_lap_times = lap_times.query(f"lap == {lap+1}")
    time_diff = 0
    if not current_lap_times.empty:
        time_diff = int(
            current_lap_times["total_millis"].median()  # We are using MEDIAN
            - current_lap_times["total_millis"].min()
        )
    else:
        # NOTE: This should not trigger
        print(f"Error -> Y:{year}, R:{race}, I:{lap}")
        return (pd.DataFrame([]), pd.DataFrame([]))

    percentage = {
        "percentage": round((lap / lap_count) * 100),
        "accidents": 0 if is_collision else 1,
        "collisions": 1 if is_collision else 0,
    }

    gap = {
        "gap": time_diff,
        "accidents": 0 if is_collision else 1,
        "collisions": 1 if is_collision else 0,
    }

    return (pd.DataFrame([percentage]), pd.DataFrame([gap]))


def _analyze_percentages(df: pd.DataFrame) -> None:
    """Analyzes correlation between DNF Accidents/Collisions and completion percentage.

    Args:
        df (pd.DataFrame): DataFrame containing accidents, collisions and completion
            percentages.
    """

    # Display a line plot for percentage completed correlation
    inc = df["accidents"].sum()
    inc_fl = df["accidents"].iloc[0]
    inc_r = inc - inc_fl
    col = round(df["collisions"].sum())
    col_fl = round(df["collisions"].iloc[0])
    col_r = col - col_fl

    corr = round(df["accidents"].corr(df["collisions"]) * 100, 2)
    corr_nf = round(df.iloc[1:]["accidents"].corr(df.iloc[1:]["collisions"]) * 100, 2)

    text = textwrap.dedent(
        f"""
        {inc} Accidents and {col} Collisions.
        {inc_fl} Accidents and {col_fl} Collisions occured on the first lap.
        {inc_r} Accidents and {col_r} Collisions occured on the remainder of laps.
        {corr}% correlation. {corr_nf}% correlation first lap ommited.
        """
    )

    # Calculating simple moving average
    df["accidents_SMA30"] = df["accidents"].rolling(10, center=True).mean()
    df["collisions_SMA30"] = df["collisions"].rolling(10, center=True).mean()

    _, ax = plt.subplots(figsize=IMAGES_DNFS_SIZE, dpi=IMAGES_DPI)
    ax.plot(df["percentage"], df["accidents_SMA30"], color="g", zorder=2, alpha=1)
    ax.plot(df["percentage"], df["collisions_SMA30"], color="r", zorder=2, alpha=1)
    ax.plot(df["percentage"], df["accidents"], color="g", alpha=0.35, zorder=1)
    ax.plot(df["percentage"], df["collisions"], color="r", alpha=0.35, zorder=1)
    ax.legend(["Accidents", "Collisions"])
    plt.title("Accidents and Collisions over race completion percentage")
    plt.xlabel("Percentage of the race completed")
    plt.ylabel("DNFS")
    plt.text(
        0.5,
        0.99,
        text,
        ha="center",
        va="top",
        transform=ax.transAxes,
    )
    print(text)
    plt.ylim([0, 35])
    plt.savefig(
        f"{IMAGES_DNFS_FOLDER}/percentages.png",
        dpi=IMAGES_DPI,
    )


def _analyze_gaps(df: pd.DataFrame) -> None:
    """Analyzes correlation between DNF Accidents/Collisions and completion percentage.

    Args:
        df (pd.DataFrame): DataFrame containing accidents, collisions and median gaps.
    """

    # Split into bins of equal time gaps and calculate sum of accidents and collisions
    # in them. We will draw that in bar plot.
    df["bins"] = pd.qcut(df["gap"], q=10)
    grouped = df.groupby(["bins"])
    res = pd.DataFrame()
    for name, group in grouped:
        bin_label = pd.to_datetime(name.right.astype(np.int64), unit="ms").strftime(
            "%M:%S:%f"
        )[:-3]

        item = pd.DataFrame(
            [
                {
                    "bin": name,
                    "binLabel": bin_label,
                    "accidents": group["accidents"].sum(),
                    "collisions": group["collisions"].sum(),
                }
            ]
        )
        res = pd.concat([res, item])

    # Display text
    text = textwrap.dedent(
        f"""
        {res['accidents'].max()} Accidents and {res['collisions'].max()} Collisions.
        {round(res["accidents"].corr(res["collisions"]) * 100, 2)}% correlation.
        """
    )

    width = 0.35
    x = np.arange(len(res["binLabel"]))
    _, ax = plt.subplots(figsize=IMAGES_DNFS_SIZE, dpi=IMAGES_DPI)
    ax.bar(x - width / 2, res["accidents"], width, label="Accidents", color="g")
    ax.bar(x + width / 2, res["collisions"], width, label="Collisions", color="r")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(res["binLabel"])
    ax.legend()
    plt.title("Accidents and Collisions over median gap to leader")
    plt.xlabel("Median gap to leader (upper/right interval limit)")
    plt.ylabel("DNFS")
    plt.text(
        0.5,
        0.99,
        text,
        ha="center",
        va="top",
        transform=ax.transAxes,
    )
    print(text)
    plt.savefig(
        f"{IMAGES_DNFS_FOLDER}/gaps.png",
        dpi=IMAGES_DPI,
    )


def analyze(force_generate_dataset: bool = False) -> None:
    if not os.path.exists(IMAGES_DNFS_FOLDER):
        os.makedirs(IMAGES_DNFS_FOLDER)

    if (
        not os.path.exists(PERCENTAGES_CSV)
        or not os.path.exists(GAPS_CSV)
        or force_generate_dataset
    ):
        print("DNFs CSVs not found, generating dataset.")
        percentages, gaps = generate_dataset()
    else:
        percentages = pd.read_csv(PERCENTAGES_CSV)
        gaps = pd.read_csv(GAPS_CSV)

    _analyze_percentages(percentages)
    _analyze_gaps(gaps)


if __name__ == "__main__":
    analyze()
