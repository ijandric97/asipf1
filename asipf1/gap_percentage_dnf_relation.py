import datetime
import os
import textwrap

import ergast
import matplotlib.pyplot as plt
import pandas as pd
from constants import (
    GAPS_AND_INCIDENTS_COLLISIONS_CSV,
    GAPS_AND_INCIDENTS_CSV,
    GAPS_NO_FIRST_COLLISIONS_CSV,
    GAPS_NO_FIRST_CSV,
    IMAGES_DPI,
    IMAGES_FOLDER,
    IMAGES_SIZE,
    PERCENTAGES_INCIDENTS_COLLISIONS_CSV,
    PERCENTAGES_INCIDENTS_CSV,
    STATUS_CODES,
    STATUS_CODES_COLLISIONS,
)


def generate_dataset(
    collisions: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    gaps_incidents_dict: dict = dict()
    percentages_incidents_dict: dict = dict()
    gaps_no_first_dict: dict = dict()

    max_season = ergast.season_list()["year"].max()
    status_codes = STATUS_CODES_COLLISIONS if collisions else STATUS_CODES

    print(f"Generating data from 1996 till {max_season}")
    # Lap Time data is available from 96
    for year in range(1996, max_season + 1):
        print(f"Parsing year {year}:")
        # Get number of races in a given season
        race_count = len(ergast.race_schedule(year=year).index)

        for race in range(1, race_count + 1):  # Rounds are 1-index based
            print(f"\tParsing round {race}")
            # Load lap data and add total time column
            lap_times = ergast.lap_times(year, race)
            if lap_times.empty:
                # Skip because no lap time data is available
                continue

            agg_df = pd.DataFrame(
                lap_times.groupby(["driverId", "lap"], as_index=False)["millis"].sum()
            )
            agg_df["total_millis"] = agg_df.groupby("driverId")["millis"].cumsum()
            lap_times = lap_times.merge(agg_df, on=["driverId", "lap", "millis"])

            # Get incident laps
            incident_laps = (
                ergast.race_results(year=year, race=race)
                .query(f"statusId in {status_codes}")
                .sort_values(by=["laps"])
                .reset_index(drop=True)
            )["laps"].to_list()

            max_laps = lap_times["lap"].max()
            for lap in incident_laps:
                # We are looking at the end of completed lap, this fixes the 0 lap issue
                current_lap_times = lap_times.query(f"lap == {lap+1}")
                time_diff = 0
                if not current_lap_times.empty:
                    time_diff = int(
                        current_lap_times["total_millis"].max()
                        - current_lap_times["total_millis"].min()
                    )
                else:
                    # NOTE: This should not trigger
                    print(f"Error -> Y:{year}, R:{race}, I:{lap}")

                gaps_incidents_dict[time_diff] = (
                    gaps_incidents_dict[time_diff] + 1
                    if time_diff in gaps_incidents_dict
                    else 1
                )

                if lap > 0:
                    gaps_no_first_dict[time_diff] = (
                        gaps_no_first_dict[time_diff] + 1
                        if time_diff in gaps_no_first_dict
                        else 1
                    )

                # We also want to see correlation between race and race ending incidents
                percentages_incidents_dict[round((lap / max_laps) * 100)] = (
                    percentages_incidents_dict[lap] + 1
                    if lap in percentages_incidents_dict
                    else 1
                )

    print("Cleaning up and creating CSV files")

    # Sort the dict by gap to leader
    # transform to dataframe, rename the columns
    # appropriately, convert milliseconds to human readable time, then export to CSV
    gaps_incidents_dict = dict(sorted(gaps_incidents_dict.items()))
    gaps_no_first_dict = dict(sorted(gaps_no_first_dict.items()))
    percentages_incidents_dict = dict(sorted(percentages_incidents_dict.items()))

    # Convert to pandas series, rename the index to GapToLeader
    gaps_incidents_series = pd.Series(gaps_incidents_dict, name="Incidents")
    gaps_incidents_series.index.name = "GapToLeader"
    gaps_no_first_series = pd.Series(gaps_no_first_dict, name="Incidents")
    gaps_no_first_series.index.name = "GapToLeader"
    percentages_incidents_series = pd.Series(
        percentages_incidents_dict, name="Incidents"
    )
    percentages_incidents_series.index.name = "Percentage"

    # Convert to pandas dataframe, reset_index to push index column to normal column
    gaps_incidents_frame = gaps_incidents_series.to_frame()
    gaps_incidents_frame = gaps_incidents_frame.reset_index()
    gaps_no_first_frame = gaps_no_first_series.to_frame()
    gaps_no_first_frame = gaps_no_first_frame.reset_index()
    percentages_incidents_frame = percentages_incidents_series.to_frame()
    percentages_incidents_frame = percentages_incidents_frame.reset_index()

    # Esentially 'resamples' from min to max index and fills missing incident count
    # with 0
    t = pd.DataFrame(
        list(
            range(
                0,
                gaps_incidents_frame["GapToLeader"].max() + 1,
            )
        ),
        columns=["GapToLeader"],
    )
    gaps_incidents_frame = pd.merge(t, gaps_incidents_frame, how="outer").fillna(
        value={"Incidents": 0}
    )
    gaps_incidents_frame.drop(
        gaps_incidents_frame.columns[
            gaps_incidents_frame.columns.str.contains("unnamed", case=False)
        ],
        axis=1,
        inplace=True,
    )
    t = pd.DataFrame(
        list(
            range(
                0,
                gaps_no_first_frame["GapToLeader"].max() + 1,
            )
        ),
        columns=["GapToLeader"],
    )
    gaps_no_first_frame = pd.merge(t, gaps_no_first_frame, how="outer").fillna(
        value={"Incidents": 0}
    )
    gaps_no_first_frame.drop(
        gaps_no_first_frame.columns[
            gaps_no_first_frame.columns.str.contains("unnamed", case=False)
        ],
        axis=1,
        inplace=True,
    )
    t = pd.DataFrame(
        list(
            range(
                0,
                100,
            )
        ),
        columns=["Percentage"],
    )
    percentages_incidents_frame = pd.merge(
        t, percentages_incidents_frame, how="outer"
    ).fillna(value={"Incidents": 0})
    percentages_incidents_frame.drop(
        percentages_incidents_frame.columns[
            percentages_incidents_frame.columns.str.contains("unnamed", case=False)
        ],
        axis=1,
        inplace=True,
    )

    # Convert Gap to Leader to human readable time
    gaps_incidents_frame["GapToLeaderText"] = gaps_incidents_frame["GapToLeader"].apply(
        lambda x: datetime.datetime.fromtimestamp(x / 1000.0).strftime("%M:%S.%f")[:-3]
    )
    gaps_no_first_frame["GapToLeaderText"] = gaps_no_first_frame["GapToLeader"].apply(
        lambda x: datetime.datetime.fromtimestamp(x / 1000.0).strftime("%M:%S.%f")[:-3]
    )

    # export the dataframe to CSV
    if collisions:
        gaps_incidents_frame.to_csv(GAPS_AND_INCIDENTS_COLLISIONS_CSV, index=False)
        gaps_no_first_frame.to_csv(GAPS_NO_FIRST_COLLISIONS_CSV, index=False)
        percentages_incidents_frame.to_csv(
            PERCENTAGES_INCIDENTS_COLLISIONS_CSV, index=False
        )
    else:
        gaps_incidents_frame.to_csv(GAPS_AND_INCIDENTS_CSV, index=False)
        gaps_no_first_frame.to_csv(GAPS_NO_FIRST_CSV, index=False)
        percentages_incidents_frame.to_csv(PERCENTAGES_INCIDENTS_CSV, index=False)

    print("Done generating datasets")
    return (gaps_incidents_frame, percentages_incidents_frame, gaps_no_first_frame)


def _load_from_csv(
    collisions: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads the DNF incident correlation data form the already generated CSV files.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Tuple containing correlation data for DNFs
        and GapToLeader and DNFs and race completion percentages.
    """
    if collisions:
        return (
            pd.read_csv(GAPS_AND_INCIDENTS_COLLISIONS_CSV),
            pd.read_csv(PERCENTAGES_INCIDENTS_COLLISIONS_CSV),
            pd.read_csv(GAPS_NO_FIRST_COLLISIONS_CSV),
        )
    else:
        return (
            pd.read_csv(GAPS_AND_INCIDENTS_CSV),
            pd.read_csv(PERCENTAGES_INCIDENTS_CSV),
            pd.read_csv(GAPS_NO_FIRST_CSV),
        )


def _analyze_gaps(df: pd.DataFrame, collisions: bool = False) -> None:
    """Analyzes correlation between DNF incidents and gap to the leader

    Args:
        df (pd.DataFrame): DataFrame containing GapToLeader and Incidents correlation
    """

    dnf_type = "Collisions/Incidents" if collisions else "Incidents"

    # Display a line plot for gap to leader correlation
    ax = df.plot.line(
        title=f"Correlation between DNF {dnf_type} and gap to the leader",
        x="GapToLeaderText",
        xlabel="Gap between the leader and the last place",
        y="Incidents",
        ylabel=f"DNF {dnf_type}",
        use_index=True,
        figsize=IMAGES_SIZE,
    )
    ax.legend([f"{dnf_type}"])
    plt.savefig(
        f"{IMAGES_FOLDER}/gaps{'_collisions' if collisions else ''}.png", dpi=IMAGES_DPI
    )


def _analyze_no_first(
    df_gaps: pd.DataFrame, df_no_first: pd.DataFrame, collisions: bool = False
) -> None:
    """Analyzes correlation between DNF incidents and gap to the leader without
    including the first lap incidents

    Args:
        df_gaps (pd.DataFrame): DataFrame containing GapToLeader and Incidents
            correlation
        df_no_first (pd.DataFrame): DataFrame containing GapToLeader and Incidents
            correlation without first lap
    """

    dnf_type = "Collisions/Incidents" if collisions else "Incidents"

    # Display a line plot for gap to leader correlation
    ax = df_gaps.plot.line(
        title=f"Correlation between DNF {dnf_type} and gap to the leader, no first lap",
        x="GapToLeaderText",
        xlabel="Gap between the leader and the last place",
        y="Incidents",
        ylabel=f"DNF {dnf_type}",
        color="r",
        use_index=True,
        figsize=IMAGES_SIZE,
    )
    df_no_first.plot.line(
        x="GapToLeaderText",
        xlabel="Gap between the leader and the last place",
        y="Incidents",
        ylabel=f"DNF {dnf_type}",
        color="k",
        figsize=IMAGES_SIZE,
        ax=ax,
    )
    ax.legend([f"All {dnf_type}", f"Non first lap {dnf_type}"])
    plt.savefig(
        f"{IMAGES_FOLDER}/no_first{'_collisions' if collisions else ''}.png",
        dpi=IMAGES_DPI,
    )


def _analyze_percentages(df: pd.DataFrame, collisions: bool = False) -> None:
    """Analyzes correlation between DNF Incidents and completion percentage.

    Args:
        df (pd.DataFrame): DataFrame containing incidents and completion percentages.
    """

    dnf_type = "Collisions/Incidents" if collisions else "Incidents"

    # Display a line plot for percentage completed correlation
    incidents = df["Incidents"].sum()
    incidents_firstlap = df["Incidents"].iloc[0]
    incidents_rest = incidents - incidents_firstlap
    incidents_text = textwrap.dedent(
        f"""
            There were {incidents} {dnf_type}.
            {incidents_firstlap} occured on the first lap.
            {incidents_rest} occured on the remainder of laps.
            """
    )

    ax = df.plot.line(
        title=f"Correlation between DNF {dnf_type} and completion percentage",
        x="Percentage",
        xlabel="Percentage of the race completed",
        y="Incidents",
        ylabel=f"DNF {dnf_type}",
        use_index=True,
        figsize=IMAGES_SIZE,
    )
    ax.legend([f"{dnf_type}"])
    plt.text(
        0.5,
        0.99,
        incidents_text,
        ha="center",
        va="top",
        transform=ax.transAxes,
    )
    print(incidents_text)
    plt.savefig(
        f"{IMAGES_FOLDER}/percentages{'_collisions' if collisions else ''}.png",
        dpi=IMAGES_DPI,
    )


def analyze(collisions: bool = False, force_generate_dataset: bool = False) -> None:
    """
    Runs a corelation analysis between non-mechanical DNFs (i.e. race ending crashes
    or collisions) and total gap to leader (i.e. time difference between the leader and
    the last position at end of the lap in which the DNF occured).

    Args:
        force_generate_dataset (bool, optional): By default, this script will not create
        a CSV file if it already exists. Setting this to True always forces creation of
        the CSV file. Defaults to False.
    """
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)

    if collisions:
        print("Collisions included")
        # Generate Data if no CSV or force flag is set
        if (
            (not os.path.exists(GAPS_AND_INCIDENTS_COLLISIONS_CSV))
            or (not os.path.exists(PERCENTAGES_INCIDENTS_COLLISIONS_CSV))
            or (not os.path.exists(GAPS_NO_FIRST_COLLISIONS_CSV))
            or force_generate_dataset
        ):
            df_gaps, df_percentages, df_no_first = generate_dataset(collisions)
        else:
            # Load the data
            df_gaps, df_percentages, df_no_first = _load_from_csv(collisions)
    else:
        # Generate Data if no CSV or force flag is set
        if (
            (not os.path.exists(GAPS_AND_INCIDENTS_CSV))
            or (not os.path.exists(PERCENTAGES_INCIDENTS_CSV))
            or (not os.path.exists(GAPS_NO_FIRST_CSV))
            or force_generate_dataset
        ):
            df_gaps, df_percentages, df_no_first = generate_dataset()
        else:
            # Load the data
            df_gaps, df_percentages, df_no_first = _load_from_csv()

    _analyze_gaps(df_gaps, collisions)
    _analyze_percentages(df_percentages, collisions)
    _analyze_no_first(df_gaps, df_no_first, collisions)


if __name__ == "__main__":
    analyze()
    analyze(True)
