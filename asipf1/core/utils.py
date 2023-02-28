from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.constants import IMAGES_DPI, IMAGES_PITSTOPS_SIZE


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


def plot_multiple_by_time(res: pd.DataFrame, filename: str) -> None:
    avg_duration_txt = ""
    avg_count_txt = ""

    optimal_txt = (
        "Actual and optimal correlation: "
        + f"{abs(res['actualFirstPitstopLap'].corr(res['optimalFirstPitstopLap'])):.2f}"
    )
    avg_duration_txt = f"Average: {round(res['averagePitstopDuration'].mean())} ms"
    avg_count_txt = f"Average: {res['averageNumberOfPitstops'].mean():.2f}"

    colors = []
    if "hadDNFBefore" in res:
        for _, row in res.iterrows():
            colors.append("r" if row["hadDNFBefore"] else "k")

    fig = plt.figure(figsize=IMAGES_PITSTOPS_SIZE, dpi=IMAGES_DPI)
    ax = fig.add_subplot(3, 1, 1)

    ax.plot(res["year"], res["actualFirstPitstopLap"], "-o", color="k", zorder=1.5)
    ax.plot(res["year"], res["optimalFirstPitstopLap"], "-o", color="g", zorder=1.75)
    plt.legend(["Actual", "Optimal"])
    plt.axhline(
        res["actualFirstPitstopLap"].mean(),
        color="k",
        linestyle="--",
        zorder=1,
        alpha=0.5,
    )
    plt.axhline(
        res["optimalFirstPitstopLap"].mean(),
        color="g",
        linestyle="--",
        zorder=1.25,
        alpha=0.5,
    )
    ax.scatter(
        res["year"],
        res["actualFirstPitstopLap"],
        label="warning",
        color=colors,
        zorder=2,
    )
    plt.title("Actual and optimal first pit stop lap")
    plt.xlabel("Year")
    plt.ylabel("Lap")
    plt.text(
        0.5,
        0.99,
        optimal_txt,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=12,
    )

    ax = fig.add_subplot(3, 1, 2)
    ax.plot(res["year"], res["averagePitstopDuration"], "-o", color="b", zorder=1.75)
    plt.title("Average first pitstop duration")
    plt.xlabel("Year")
    plt.ylabel("Milliseconds")
    plt.text(
        0.5,
        0.99,
        avg_duration_txt,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=12,
    )

    ax = fig.add_subplot(3, 1, 3)
    ax.plot(res["year"], res["averageNumberOfPitstops"], "-o", color="b", zorder=1.75)
    plt.title("Average number of pitstops")
    plt.xlabel("Year")
    plt.ylabel("Pitstop count")
    plt.text(
        0.5,
        0.99,
        avg_count_txt,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=12,
    )

    fig.tight_layout()
    plt.savefig(filename)
    plt.close()
