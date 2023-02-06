import os

import fastf1
import fastf1.api
import fastf1.core
import fastf1.events
import pandas as pd
from constants import FASTF1_CACHE_FOLDER

# Enable cache
if not os.path.exists(FASTF1_CACHE_FOLDER):
    os.makedirs(FASTF1_CACHE_FOLDER)
fastf1.Cache.enable_cache(FASTF1_CACHE_FOLDER)

# Get round numbers etc.
# schedule = fastf1.get_event_schedule(2022, include_testing=False)
# print(schedule)

session: fastf1.events.Session = fastf1.get_session(2019, 1, "Race")
session.load()

laps: fastf1.core.Laps = session.laps
# print(laps)
# print(session.api_path)
# print(session.event)

# position: dict[str, pd.DataFrame] = fastf1.api.position_data(session.api_path)
# for driverNum, pos in position.items():
#     pos.to_csv(f"data/position/{driverNum}.csv")

# laps_data, stream_data = fastf1.api.timing_data(session.api_path)
# laps_data.to_csv("data/timing/laps_data.csv")
# stream_data.to_csv("data/timing/stream_data.csv")

laps = session.laps.pick_driver("VER")
pos_data: pd.DataFrame = laps.get_pos_data()

laps.to_csv("ver.csv")
print(pos_data)
pos_data.to_csv("ver_pos.csv")
