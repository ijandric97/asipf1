from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_local_minimum(c: np.poly1d) -> tuple[np.ndarray, np.ndarray]:
    """
    Gets local minimum of a NumPy 1D Polynomial. Should be used in conjuction with the
    polynomial regression.

    Args:
        c (np.poly1d): 1D Polynomial (probably regression etc.)

    Returns:
        tuple[np.ndarray, np.ndarray]: Tuple containing the local minimum X value and
            the Y value in the local minimum.
    """
    crit = c.deriv().r
    r_crit = crit[crit.imag == 0].real
    test = c.deriv(2)(r_crit)

    # Compute local minima, excluding range boundaries
    x_min = r_crit[test > 0]
    y_min = c(x_min)
    return (x_min, y_min)


def plot_regression(
    x: pd.Series,
    y: pd.Series,
    regression_model: np.poly1d,
    min_x: Optional[int] = None,
    title: str = "",
) -> None:
    """
    Plots x and y values against the provided regression model. Also displays the
    local minimal x value if provided.

    Args:
        x (pd.Series): _description_
        y (pd.Series): _description_
        regression_model (np.poly1d): _description_
        min_x (int): _description_
        title (str, optional): _description_. Defaults to "".
    """

    max_x = x.max() if x.max() > min_x else min_x
    first_stops_line = np.linspace(x.min(), max_x, 200)

    _, ax = plt.subplots()
    plt.title(f"{title}")
    ax.scatter(x, y)
    ax.plot(first_stops_line, regression_model(first_stops_line))
    if min_x:
        ax.scatter(min_x, regression_model(min_x), color="red")
    plt.show()
