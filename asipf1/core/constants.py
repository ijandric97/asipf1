from typing import Optional, TypedDict

import pandas as pd

DATA_FOLDER = "data"
PERCENTAGES_CSV = DATA_FOLDER + "./percentages.csv"
GAPS_CSV = DATA_FOLDER + "./gaps.csv"
PITSTOPS_CSV = DATA_FOLDER + "./pitstops.csv"

IMAGES_FOLDER = "images"
IMAGES_DNFS_FOLDER = IMAGES_FOLDER + "/gap_dnfs"
IMAGES_PITSTOPS_FOLDER = IMAGES_FOLDER + "/optimal_pitstop"

IMAGES_DPI = 100
IMAGES_DNFS_SIZE = (16, 10)
IMAGES_PITSTOPS_SIZE = (16, 20)

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
STATUS_ACCIDENTS = [3, 20, 104]
STATUS_COLLISIONS = [4, 130, 138]


class PlotData(TypedDict):
    x: pd.Series
    y: pd.Series
    title: str
    xlabel: str
    ylabel: str
    color: str
    show_mean: Optional[bool]
    text: Optional[str]
