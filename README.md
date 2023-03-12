# **ASIP F1**

## **Overview**

Formula 1 data correlation analysis project for the "Systems and Data Analysis" course at the University of Rijeka, Faculty of Engineering.

### **Objectives**

- Check if there are certain trends regarding the first pit stop.
  - Use polynomial regression to determine the optimal first pit stop lap per track
- Check if there is a correlation between non-mechanical DNFs and field density

## **Technical overview**

### **Database image file**

The f1db.sqlite is an SQLite converted ErgastDb dump downloaded from http://ergast.com/mrd/db/ which was last updated on: 2023-01-07.
The original MySQL dump is loaded using phpMyAdmin to MySQL and then exported to SQLite using the following python package: https://pypi.org/project/mysql-to-sqlite3/

Unfortunately, the database only contains the pit stop data from 2012. season onwards. Lap time data is available from 2016. season onwards.

### **How to run**

This code has only been tested on Python 3.11.

First, create a virtual environment and activate it.

```bash
$ python -m venv venv
$ source venv\bin\activate
```

Install poetry dependency manager and then dependencies using it.

```bash
pip install poetry
poetry install
```

Run the program

```
python ./asipf1/__init__.py
```

### **Generated data**

The generated CSV files can be found in the data folder.
The generated image plots can be found in the images folder.

### **First pit stop**

Lap entry is already available as a data parameter

# **Results**

## **First pit stop analysis**

### **Averages through the years**

![Pit stop averages](/docs/_pitstop_averages.png)

It is immediately noticeable that the average first pit stop duration has increased by around a second in 2014. and has remained relatively stable since then. The only reasonable explanation for such a slowdown is the pit lane limit reduction from 100km/h to 80km/h in 2014. season onwards.

Additionally, it is noticeable that the average lap time has steadily decreased since the 2014 season only to come up a bit in 2022. This analysis does not take into account the different track lengths etc. but it does match the real-life records which mostly belong to 2018. - 2020. cars, with the 2020 Mercedes W11 being the absolute fastest car to date.

Actual and optimal first lap fluctuate wildly, however, it is noticeable that there is a 77% reverse correlation between the first stop lap and the average number of pit stops, e.g. the sooner everyone pits, the more pit stops will be required.

### **Chinese Grand Prix**

![Shanghai](/docs/shanghai.png)

Chinese GP is interesting because it clearly shows that the polynomial regression model is generally correct but falls apart completely in its 2013 optimal lap prediction.

The reason for such failure is that the race was highly unpredictable, which can be clearly seen in the result of the polynomial regression.

![Shanghai 2013](/docs/shanghai_2013.png)

The first bunch of pit stop entries is around the 5th to 7th lap which correlates with a crash that happened on the 4/5th lap of the race between A. Sutil and E. Gutiérrez. The second batch of entries is related to the 14/15th lap DNF when M. Webber lost his wheel due to an improper pit stop. Lastly, the 2 drivers that have pitted around the 23rd lap have been on a different strategy altogether.

This has resulted in potentially 3 different strategies, with 1-3 stops. Polynomial regression can't produce a good result but its result still falls in the [0, max_laps-1] range, therefore it is considered valid.

### **Japanese Grand Prix**

![Suzuka](/docs/suzuka.png)

A surprisingly stable race with the exceptions of the 2 rain-affected races which happened in 2014 and 2022. Otherwise, this track shows a relatively stable first pit entry window, which is from the 15th to the 25th lap.

In both 2014 and 2022, the race has been red-flagged on the first lap which also unfortunately counts as a first pit stop. Additionally, this also caused a huge anomaly in the pitstop duration data and the results for the 2014 GP have been excluded.

### **Bahrain Grand Prix**

![Bahrain](/docs/bahrain.png)

This is a specific scenario in the COVID-19-affected 2020 and 2021 seasons where some tracks had double header weekends (e.g. the same track is completed 2 times).

This is clearly visible in the 2020 Bahrain GP. Due to the way, the database is structured it does not differentiate between track layouts therefore the short version of Bahrain GP is considered identical to the full version Bahrain GP layout. Still, it is very interesting that in both cases the actual first pit stop entry lap was the first lap. In the Sahkir GP due to a miracle drive by C. Perez and in the Bahrain GP due to R. Grosjean's first lap crash and explosion.

The optimal lap prediction should be somewhat correct. The strategy of staying long on the first set of tires and then driving fast, in the end, is exactly what Perez did but he had to do an emergency stop on the first lap because of the damage from a collision.

## **Non-mechanical DNF analysis**

First, there has to be some kind of metric for field density. Initially, this was the gap between the first and last driver, but since that can have huge outliers, the actual metric is the gap between the leader (first driver) and the median time of all the drivers. This in turn should produce a zone in which the upper half of the field is located.

The median gap at the end of the race is also taken into the account as a separate metric.

In order to check if certain parts of the race have more non-mechanical DNFs than others, the percentage at which a DNF has occurred has been taken into account (since neither lap nor race time is a normalized value).

### **Race percentage correlation**

![Percentages](/docs/percentages.png)

Since the result is rather hard to read, SMA (Simple Moving Average) has been applied and centered over the data. It is clear that the first lap is critical since 38.7% of crashes and 15.6% of accidents happened in the first lap alone. The first 5-10% of the race shows an increased chance of the DNF occurring, while the remaining 90%+ show no apparent trend.

This is also logically sound since cars are always packed extremely close together during the race start.

### **Density correlation**

![Results](/docs/results.png)

If the data is bucketed according to the median gaps at the end of the race (where each bucket consists of 50 races that ended within the specified median gap), it is clearly visible that most accidents happen when drivers are extremely close together (0-20 seconds gap). Interestingly it is also observable that when there is a very low density, there is a higher chance of a driver spinning out or crashing into the wall on his own.

![Gaps](/docs/gaps.png)

This is also observable when the data is bucketed to contain approximately the same number of DNFs. It is noticeable that the collisions and accidents are reversely correlated by about 82%, e.g. when drivers are closer there are more collisions, when drivers are far apart there are more accidents (crashing into a wall, spinning out, etc.).
