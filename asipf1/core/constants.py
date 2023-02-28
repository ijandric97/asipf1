from typing import Optional, TypedDict

import pandas as pd

DATA_FOLDER = "data"
PERCENTAGES_CSV = DATA_FOLDER + "./percentages.csv"
GAPS_CSV = DATA_FOLDER + "./gaps.csv"
PITSTOPS_CSV = DATA_FOLDER + "./pitstops.csv"
RESULTS_CSV = DATA_FOLDER + "./results.csv"

IMAGES_FOLDER = "images"
IMAGES_DNFS_FOLDER = IMAGES_FOLDER + "/gap_dnfs"
IMAGES_PITSTOPS_FOLDER = IMAGES_FOLDER + "/optimal_pitstop"

IMAGES_DPI = 100
IMAGES_DNFS_SIZE = (16, 10)
IMAGES_PITSTOPS_SIZE = (16, 20)

BAR_WIDTH = 0.35

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
#
# 'Good' finished statuses for the 1996 onwards are:
# 1 - Finished
# 11 - +1 Lap
# 12 - +2 Laps
# ...and so on till
# 18 - +8 Laps
STATUS_ACCIDENTS = [3, 20, 104]
STATUS_COLLISIONS = [4, 130, 138]
STATUS_FINISHED = [1, 11, 12, 13, 14, 15, 16, 17, 18]
POSITION_DNF = ["R", "D", "E", "W", "F", "N"]


class PlotData(TypedDict):
    x: pd.Series
    y: pd.Series
    title: str
    xlabel: str
    ylabel: str
    color: str
    show_mean: Optional[bool]
    text: Optional[str]
