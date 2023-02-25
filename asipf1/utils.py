import textwrap
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from constants import IMAGES_DPI, IMAGES_PITSTOPS_FOLDER, IMAGES_SIZE, PlotData


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


def plot_multiple(
    plots: list[PlotData],
    filename: str,
    figsize: tuple[int, int] = IMAGES_SIZE,
    dpi: int = IMAGES_DPI,
) -> None:
    fig = plt.figure(figsize=figsize, dpi=dpi)
    for i, data in enumerate(plots):
        ax = fig.add_subplot(len(plots), 1, i + 1)
        ax.plot(data["x"], data["y"], "-o", color=data["color"])
        plt.title(data["title"])
        plt.xlabel(data["xlabel"])
        plt.ylabel(data["ylabel"])
        if "show_mean" in data:
            plt.axhline(data["y"].mean(), color=data["color"], linestyle="--")
        if "text" in data:
            plt.text(
                0.5,
                0.99,
                data["text"],
                ha="center",
                va="top",
                transform=ax.transAxes,
            )

    fig.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_multiple_by_time(res: pd.DataFrame, filename: str) -> None:
    avg_duration_txt = ""
    avg_count_txt = ""

    if res["year"].min() < 2010 and res["year"].max() >= 2010:
        avg_duration_txt = textwrap.dedent(
            f"""
            Refuelling average: {
                round(res[res['year'] < 2010]["averagePitstopDuration"].mean())} ms
            No reffuelling average: {
                round(res[res['year'] >= 2010]["averagePitstopDuration"].mean())} ms
            """
        )
        avg_count_txt = textwrap.dedent(
            f"""
            Refuelling average: {
                res[res['year'] < 2010]["averageNumberOfPitstops"].mean():.2f}
            No reffuelling average: {
                res[res['year'] >= 2010]["averageNumberOfPitstops"].mean():.2f}
            """
        )

    plot_multiple(
        [
            {
                "x": res["year"],
                "y": res["optimalFirstPitstopLap"],
                "title": "Optimal first pit stop lap",
                "xlabel": "Year",
                "ylabel": "Lap",
                "color": "g",
                "show_mean": True,
            },
            {
                "x": res["year"],
                "y": res["actualFirstPitstopLap"],
                "title": "Actual first pit stop lap",
                "xlabel": "Year",
                "ylabel": "Lap",
                "color": "r",
                "show_mean": True,
            },
            {
                "x": res["year"],
                "y": res["averagePitstopDuration"],
                "title": "Average first pitstop duration",
                "xlabel": "Year",
                "ylabel": "Milliseconds",
                "color": "b",
                "text": avg_duration_txt,
            },
            {
                "x": res["year"],
                "y": res["averageNumberOfPitstops"],
                "title": "Average number of pitstops",
                "xlabel": "Year",
                "ylabel": "Pitstop count",
                "color": "b",
                "text": avg_count_txt,
            },
        ],
        filename,
    )
