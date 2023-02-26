from typing import Optional, TypedDict

import pandas as pd

DATA_FOLDER = "data"
GAPS_AND_INCIDENTS_CSV = DATA_FOLDER + "/gaps_and_incidents.csv"
GAPS_AND_INCIDENTS_COLLISIONS_CSV = DATA_FOLDER + "/gaps_and_incidents_collisions.csv"
GAPS_NO_FIRST_CSV = DATA_FOLDER + "/gaps_no_first.csv"
GAPS_NO_FIRST_COLLISIONS_CSV = DATA_FOLDER + "/gaps_no_first_collisions.csv"
PERCENTAGES_INCIDENTS_CSV = DATA_FOLDER + "/percentages_and_incidents.csv"
PERCENTAGES_INCIDENTS_COLLISIONS_CSV = (
    DATA_FOLDER + "/percentages_and_incidents_collisions.csv"
)

PITSTOPS_CSV = DATA_FOLDER + "./pitstops.csv"

IMAGES_FOLDER = "images"
IMAGES_DPI = 100

IMAGES_PITSTOPS_FOLDER = IMAGES_FOLDER + "/optimal_pitstop"
IMAGES_PITSTOPS_SIZE = (16, 20)

IMAGES_SIZE = (16, 10)


FASTF1_CACHE_FOLDER = ".cache"

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
STATUS_CODES = [3, 20, 104]
STATUS_CODES_COLLISIONS = [3, 4, 20, 104]


class PlotData(TypedDict):
    x: pd.Series
    y: pd.Series
    title: str
    xlabel: str
    ylabel: str
    color: str
    show_mean: Optional[bool]
    text: Optional[str]
