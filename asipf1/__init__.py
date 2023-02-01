import datetime

import ergast
import matplotlib.pyplot as plt
import pandas as pd

DATA_FOLDER = "data"
GAPS_AND_INCIDENTS_CSV = DATA_FOLDER + "/gaps_and_incidents.csv"

# We are looking for the following statueses:
# 3 - Accident -> Neš se desilo i DNF je ishod, znači najčešće izletio u zid (Senna 94)
# 4 - Collision -> 2 or more cars crashed into each other
# 20 - Spun off -> Car got stuck in the gravel and DNF
#
# We can ignore these statuses for now:
# 104 - Fatal accident -> Death has to be pronunced at the spot not in the hospital
#                      -> Therefore Bianchi for example does not count
#                      -> No such cases between 96-22
# 130 - Collision Damage -> When driver collided with another driver but managed to
#                           continue running for additional lap(s) until the car gave up
# 138 - Debris -> Only 1 such case, which is Russell 2020 when he got hit by a loose
#                 wheel from another car
STATUS_CODES = [3, 4, 20, 104]

########################################################################################
def generate_dataset() -> pd.DataFrame:
    gaps_incidents_dict: dict = dict()

    # Lap Time data is available from 96
    for year in range(1996, 2023):
        # Get number of races in a given season
        round_count = len(ergast.race_schedule(year=year).index)
        for round in range(1, round_count + 1):  # Rounds are 1-index based
            # Load lap data and add total time column
            lap_times = ergast.lap_times(year, round)
            agg_df = pd.DataFrame(
                lap_times.groupby(["driverId", "lap"], as_index=False)["millis"].sum()
            )
            agg_df["total_millis"] = agg_df.groupby("driverId")["millis"].cumsum()
            lap_times = lap_times.merge(agg_df, on=["driverId", "lap", "millis"])

            # Get incident laps
            incident_laps = (
                ergast.race_results(year=year, round=round)
                .query(f"statusId in {STATUS_CODES}")
                .sort_values(by=["laps"])
                .reset_index(drop=True)
            )["laps"].to_list()

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
                    print(f"Error -> Y:{year}, R:{round}, I:{lap}")

                gaps_incidents_dict[time_diff] = (
                    gaps_incidents_dict[time_diff] + 1
                    if time_diff in gaps_incidents_dict
                    else 1
                )

    # Sort the dict by gap to leader
    # transform to dataframe, rename the columns
    # appropriately, convert milliseconds to human readable time, then export to CSV
    gaps_incidents_dict = dict(sorted(gaps_incidents_dict.items()))

    # Convert to pandas series, rename the index to GapToLeader
    gaps_incidents_series = pd.Series(gaps_incidents_dict, name="Incidents")
    gaps_incidents_series.index.name = "GapToLeader"

    # Convert to pandas dataframe, reset_index to push index column to normal column
    gaps_incidents_frame = gaps_incidents_series.to_frame()
    gaps_incidents_frame = gaps_incidents_frame.reset_index()

    # Esentially 'resamples' from min to max index and fills missing incident count with 0
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

    # Convert Gap to Leader to human readable time
    gaps_incidents_frame["GapToLeaderText"] = gaps_incidents_frame["GapToLeader"].apply(
        lambda x: datetime.datetime.fromtimestamp(x / 1000.0).strftime("%M:%S.%f")[:-3]
    )

    # export the dataframe to CSV
    gaps_incidents_frame.to_csv(GAPS_AND_INCIDENTS_CSV)

    return gaps_incidents_frame


# Generate Data
# df = generate_dataset()

# Load data
df = pd.read_csv(GAPS_AND_INCIDENTS_CSV)

# Display a plot
df.plot.line(x="GapToLeaderText", y="Incidents", use_index=True)
plt.show()
