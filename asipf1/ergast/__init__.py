import json
import textwrap
from typing import Optional

import pandas as pd
from ergast.db import con


def season_list(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    constructorStanding: Optional[int] = None,
    driverStanding: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain a list of seasons for a given query.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        constructorStanding (Optional[int], optional): Limit results by a final
            CDC finishing position (e.g. only constructors that have finished in 3rd
            place). Defaults to None.
        driverStanding (Optional[int], optional): Limit results by a final WDC position
            (e.g. only drivers that have finished a season in 3rd place).
            Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Raises:
        ValueError: Cannot combine standings with circuit, grid, result or status qualifiers.

    Returns:
        pd.DataFrame: Pandas DataFrame with list of seasons for the given criteria.
    """

    if (driverStanding or constructorStanding) and (
        circuit or grid or fastest or result or status
    ):
        raise ValueError(
            "Cannot combine standings with circuit, grid, result or status qualifiers."
        )

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT s.year, s.url
        FROM seasons s
        {", drivers dr" if driver else ""}
        {", constructors co" if constructor else ""}
        """
    )

    if driverStanding or constructorStanding:
        query = textwrap.dedent(
            f"""
            {query}
            , races ra
            {", driverStandings ds" if driverStanding or driver else ""}
            {", constructorStandings cs" if constructorStanding or constructor else ""}
            """
        )
    else:
        query = textwrap.dedent(
            f"""
            {query}
            {", races ra" if year or circuit or driver or constructor or status or result or grid or fastest else ""}
            {", results re" if driver or constructor or status or result or grid or fastest else ""}
            {", circuits ci" if circuit else ""}
            """
        )
    query += " WHERE TRUE"

    if driverStanding or constructorStanding:
        query = textwrap.dedent(
            f"""
            {query}
            AND s.year=ra.year
            {"AND cs.raceId=ra.raceId" if constructorStanding or constructor else ""}
            {f"AND cs.constructorId=co.constructorId AND co.constructorRef='{constructor}'" if constructor else ""}
            {f"AND cs.positionText='{constructorStanding}'" if constructorStanding else ""}
            {"AND ds.raceId=ra.raceId" if driverStanding or driver else ""}
            {f"AND ds.driverId=dr.driverId AND dr.driverRef='{driver}'" if driver else ""}
            {f"AND ds.positionText='{driverStanding}'" if driverStanding else ""}
            {f"AND s.year='{year}'" if year else ""}
            {f"AND ra.round='{race}'" if race else (f"AND ra.round=(SELECT MAX(round) FROM races WHERE races.year='{year}')" if year else "AND (ra.year, ra.round) IN (SELECT year, MAX(round) FROM races GROUP BY year)")}
            """
        )
    else:
        query = textwrap.dedent(
            f"""
            {query}
            {"AND s.year=ra.year" if year or circuit or driver or constructor or status or result or grid or fastest else ""}
            {f"AND ra.circuitId=ci.circuitId AND ci.circuitRef='{circuit}'" if circuit else ""}
            {"AND ra.raceId=re.raceId" if driver or constructor or status or result or grid or fastest else ""}
            {f"AND re.constructorId=co.constructorId AND co.constructorRef='{constructor}'" if constructor else ""}
            {f"AND re.driverId=dr.driverId AND dr.driverRef='{driver}'" if driver else ""}
            {f"AND re.statusId='{status}'" if status else ""}
            {f"AND re.grid='{grid}'" if grid else ""}
            {f"AND re.rank='{fastest}'" if fastest else ""}
            {f"AND re.positionText='{result}'" if result else ""}
            {f"AND s.year='{year}'" if year else ""}
            {f"AND ra.round='{race}'" if race else ""}
            """
        )

    query = textwrap.dedent(
        f"""
        {query}
        ORDER BY s.year
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "year",
            "url",
        ],
    )
    return df


def race_schedule(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain the race schedule for the specified year or query.

    Args:
        year (Optional[int], optional): Season calendar year. Should be from 2003
            onwards. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with race schedule for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT
        ra.year, ra.round, ra.name, ra.date, ra.time, ra.url,
        c.circuitRef, c.name, c.location, c.country, c.lat, c.lng, c.alt, c.url
        FROM races ra, circuits c
        {", results re" if driver or constructor or grid or result or status or fastest else ""}
        {", drivers" if driver else ""}
        {", constructors" if constructor else ""}
        WHERE ra.circuitId=c.circuitId
        {f"AND ra.year='{year}'" if year else ""}
        {f"AND ra.round='{race}'" if race else ""}
        {f"AND c.circuitRef='{circuit}'" if circuit else ""}
        {"AND ra.raceId=re.raceId" if driver or constructor or grid or result or status or fastest else ""}
        {f"AND re.constructorId=constructors.constructorId AND constructors.constructorRef='{constructor}'" if constructor else ""}
        {f"AND re.driverId=drivers.driverId AND drivers.driverRef='{driver}'" if driver else ""}
        {f"AND re.statusId='{status}'" if status else ""}
        {f"AND re.grid='{grid}'" if grid else ""}
        {f"AND re.rank='{fastest}'" if fastest else ""}
        {f"AND re.positionText='{result}'" if result else ""}
        ORDER BY ra.year, ra.round
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "year",
            "round",
            "raceName",
            "date",
            "time",
            "url",
            "circuitId",
            "circuitName",
            "location",
            "country",
            "lat",
            "long",
            "altitude",
            "circuitUrl",
        ],
    )
    return df


def race_results(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain the race results for the specified race or query.
    If the results for the specified race are not yet available the result will be empty.

    The value of the position attribute in the Result element is always an integer,
    giving the finishing order of all drivers.

    The value of the positionText attribute is either:
    * An integer (finishing position)
    * "R" (retired)
    * "D" (disqualified)
    * "E" (excluded)
    * "W" (withdrawn)
    * "F" (failed to qualify)
    * "N" (not classified).
    Further information is given by the status element.

    A grid position value of "0" indicates the driver started from the pit lane.

    Fastest lap times are included from the 2004 season onwards.
    The <rank> value refers to how the fastest lap for each driver is ranked in relation
    to those of other drivers.

    Drivers who participated in the 2014 season onwards have a permanent driver number.
    For these drivers there is a corresponding field in the Driver element. However,
    this may differ from the value of the number attribute of the Result element in
    earlier seasons or where the reigning champion has chosen to use “1” rather than
    his permanent driver number.

    Args:
        year (Optional[int], optional): Season calendar year. Should be from 2003
            onwards. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with race results for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT
        ra.year, ra.round, ra.name, ra.date, ra.time, ra.url, 
        ci.circuitRef, ci.name, ci.location, ci.country, ci.url, ci.lat, ci.lng, ci.alt,
        re.grid, re.positionText, re.positionOrder, re.number, re.points, re.laps, re.time, re.milliseconds, re.rank, re.fastestLap, re.fastestLapTime, re.fastestLapSpeed,
        dr.driverRef, dr.number, dr.code, dr.forename, dr.surname, dr.dob, dr.nationality, dr.url,
        st.statusId, st.status,
        co.constructorRef, co.name, co.nationality, co.url
        FROM races ra, circuits ci, results re, drivers dr, constructors co, status st
        WHERE ra.circuitId=ci.circuitId
        AND ra.raceId=re.raceId
        AND re.driverId=dr.driverId
        AND re.constructorId=co.constructorId
        AND re.statusId=st.statusId
        {f"AND ra.year='{year}'" if year else ""}
        {f"AND ra.round='{race}'" if race else ""}
        {f"AND ci.circuitRef='{circuit}'" if circuit else ""}
        {f"AND co.constructorRef='{constructor}'" if constructor else ""}
        {f"AND dr.driverRef='{driver}'" if driver else ""}
        {f"AND re.statusId='{status}'" if status else ""}
        {f"AND re.grid='{grid}'" if grid else ""}
        {f"AND re.rank='{fastest}'" if fastest else ""}
        {f"AND re.positionText='{result}'" if result else ""}
        ORDER BY ra.year, ra.round, re.positionOrder
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "year",
            "round",
            "raceName",
            "date",
            "time",
            "url",
            "circuitId",
            "circuitName",
            "locality",
            "country",
            "circuitUrl",
            "lat",
            "long",
            "altitude",
            "grid",
            "positionText",
            "position",
            "carNumber",
            "points",
            "laps",
            "time",
            "timeMillis",
            "fastestLapRank",
            "fastestLap",
            "fastestLapTime",
            "fastestLapSpeed",
            "driverId",
            "driverNumber",
            "driverCode",
            "givenName",
            "familyName",
            "dateOfBirth",
            "nationality",
            "driverUrl",
            "statusId",
            "status",
            "constructorId",
            "constructorName",
            "constructorNationality",
            "constructorUrl",
        ],
    )
    return df


def qualifying_results(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain the qualifyng results for the specified race or query.
    If the qualifying results for the specified race are not available the result will
    be empty.
    Note that the starting grid positions may be different to the qualifying positions,
    due to penalties or mechanical problems. The starting grid positions are recorded
    in the grid field in the Race Results.
    Note that Qualifying results are only fully supported from the 2003 season onwards.

    Args:
        year (Optional[int], optional): Season calendar year. Should be from 2003
            onwards. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with qualifying results for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT
            ra.year, ra.round, ra.name, ra.date, ra.time, ra.url, 
            ci.circuitRef, ci.name, ci.location, ci.country, ci.url, ci.lat, ci.lng, ci.alt,
            qu.number, qu.position, qu.q1, qu.q2, qu.q3,
            dr.driverRef, dr.number, dr.code, dr.forename, dr.surname, dr.dob, dr.nationality, dr.url,
            co.constructorRef, co.name, co.nationality, co.url
        FROM races ra, circuits ci, qualifying qu, drivers dr, constructors co
        {", results re" if grid or result or status or fastest else ""}
        WHERE ra.circuitId=ci.circuitId
        AND qu.raceId=ra.raceId
        AND qu.driverId=dr.driverId
        AND qu.constructorId=co.constructorId
        {"AND re.raceId=qu.raceId AND re.driverId=qu.driverId AND re.constructorId=qu.constructorId" if grid or result or status or fastest else ""}
        {f"AND ra.year='{year}'" if year else ""}
        {f"AND ra.round='{race}'" if race else ""}
        {f"AND ci.circuitRef='{circuit}'" if circuit else ""}
        {f"AND co.constructorRef='{constructor}'" if constructor else ""}
        {f"AND dr.driverRef='{driver}'" if driver else ""}
        {f"AND re.statusId='{status}'" if status else ""}
        {f"AND re.grid='{grid}'" if grid else ""}
        {f"AND re.rank='{fastest}'" if fastest else ""}
        {f"AND re.positionText='{result}'" if result else ""}
        ORDER BY ra.year, ra.round, qu.position
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "year",
            "round",
            "raceName",
            "date",
            "time",
            "url",
            "circuitId",
            "circuitName",
            "locality",
            "country",
            "circuitUrl",
            "lat",
            "long",
            "altitude",
            "carNumber",
            "position",
            "q1",
            "q2",
            "q3",
            "driverId",
            "driverNumber",
            "driverCode",
            "givenName",
            "familyName",
            "dateOfBirth",
            "nationality",
            "driverUrl",
            "constructorId",
            "constructorName",
            "constructorNationality",
            "constructorUrl",
        ],
    )
    return df


def driver_standings(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    driver: Optional[str] = None,
    driverStanding: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Lists the driver standings.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        driverStanding (Optional[int], optional): Limit results by a final WDC position
            (e.g. only drivers that have finished a season in 3rd place).
            Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with list of drive standings for the given
            criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT
        d.driverId, d.driverRef, d.number, d.code, d.forename, d.surname, d.dob, d.nationality, d.url,
        ds.points, ds.position, ds.positionText, ds.wins, r.year, r.round
        FROM drivers d, driverStandings ds, races r
        WHERE ds.raceId=r.raceId AND ds.driverId=d.driverId
        {f"AND ds.positionText='{driverStanding}'" if driverStanding else ""}
        {f"AND d.driverRef='{driver}'" if driver else ""}
        {f"AND r.year='{year}'" if year else ""}
        {f"AND r.round='{race}'" if race else (f"AND r.round=(SELECT MAX(round) FROM driverStandings ds, races r WHERE ds.raceId=r.raceId AND r.year='{year}')" if year else "AND (r.year, r.round) IN (SELECT year, MAX(round) FROM races GROUP BY year)")}
        ORDER BY r.year, ds.position
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "driverInternalId",
            "driverId",
            "permanentNumber",
            "driverCode",
            "givenName",
            "familyName",
            "dateOfBirth",
            "nationality",
            "url",
            "points",
            "position",
            "positionText",
            "wins",
            "year",
            "round",
        ],
    )
    return df


def constructor_standings(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    constructor: Optional[str] = None,
    constructorStanding: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Lists the constructor standings.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        constructorStanding (Optional[int], optional): Limit results by a final
            CDC finishing position (e.g. only constructors that have finished in 3rd
            place). Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with list of constructor standings for the given
            criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT
            c.constructorRef, c.name, c.nationality, c.url,
            cs.points, cs.position, cs.positionText, cs.wins,
            r.year, r.round
        FROM constructors c, constructorStandings cs, races r
        WHERE cs.raceId=r.raceId AND cs.constructorId=c.constructorId
        {f"AND cs.positionText='{constructorStanding}'" if constructorStanding else ""}
        {f"AND c.constructorRef='{constructor}'" if constructor else ""}
        {f"AND r.year='{year}'" if year else ""}
        {f"AND r.round='{race}'" if race else (f"AND r.round=(SELECT MAX(round) FROM driverStandings ds, races r WHERE ds.raceId=r.raceId AND r.year='{year}')" if year else "AND (r.year, r.round) IN (SELECT year, MAX(round) FROM races GROUP BY year)")}
        ORDER BY r.year, cs.position
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "constructorId",
            "constructorName",
            "nationality",
            "url",
            "points",
            "position",
            "positionText",
            "wins",
            "year",
            "round",
        ],
    )
    return df


def driver_information(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    constructorStanding: Optional[int] = None,
    driverStanding: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain a list of all drivers within a series, year or round.
    Each driver listed is identified by a unique driverId which is used to identify the
    driver throughout the API.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        constructorStanding (Optional[int], optional): Limit results by a final
            CDC finishing position (e.g. only constructors that have finished in 3rd
            place). Defaults to None.
        driverStanding (Optional[int], optional): Limit results by a final WDC position
            (e.g. only drivers that have finished a season in 3rd place).
            Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Raises:
        ValueError: Cannot combine standings with circuit, grid, result or status qualifiers.

    Returns:
        pd.DataFrame: Pandas DataFrame with list of drivers for the given criteria.
    """

    if (driverStanding or constructorStanding) and (
        circuit or grid or result or status
    ):
        raise ValueError(
            "Bad Request: Cannot combine standings with circuit, grid, result or status qualifiers."
        )

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT
        dr.driverRef, dr.number, dr.code, dr.forename, dr.surname, dr.dob, dr.nationality, dr.url
        FROM drivers dr
        {", results re" if year or constructor or status or grid or result or circuit or fastest else ""}
        {", races ra" if year or circuit or driverStanding or constructorStanding else ""}
        {", driverStandings ds" if driverStanding or constructorStanding else ""}
        {", constructorStandings cs" if constructorStanding else ""}
        {", circuits ci" if circuit else ""}
        {", constructors co" if constructor else ""}
        WHERE TRUE
        """
    )

    if driverStanding or constructorStanding:
        query = textwrap.dedent(
            f"""
            {query}
            {"AND dr.driverId=re.driverId" if year or constructor else ""}
            {"AND re.raceId=ra.raceId" if year else ""}
            {f"AND re.constructorId=co.constructorId AND co.constructorRef='{constructor}'" if constructor else ""}
            {f"AND dr.driverRef='{driver}'" if driver else ""}
            {f"AND ds.positionText='{driverStanding}'" if driverStanding else ""}
            AND ds.raceId=ra.raceId
            AND dr.driverId=ds.driverId
            {f"AND cs.raceId=ra.raceId AND cs.positionText='{constructorStanding}'" if constructorStanding else ""}
            {"AND co.constructorId=cs.constructorId" if constructor and constructorStanding else ""}
            """
        )
    else:
        query = textwrap.dedent(
            f"""
            {query}
            {"AND dr.driverId=re.driverId" if year or constructor or status or grid or result or circuit or fastest else ""}
            {"AND re.raceId=ra.raceId" if year or circuit else ""}
            {f" AND ra.circuitId=ci.circuitId AND ci.circuitRef='{circuit}'" if circuit else ""}
            {f"AND re.constructorId=co.constructorId AND co.constructorRef='{constructor}'" if constructor else ""}
            {f"AND re.statusId='{status}'" if status else ""}
            {f"AND re.grid='{grid}'" if grid else ""}
            {f"AND re.rank='{fastest}'" if fastest else ""}
            {f"AND re.positionText='{result}'" if result else ""}
            {f"AND dr.driverRef='{driver}'" if driver else ""}
            """
        )

    query = textwrap.dedent(
        f"""
        {query}
        {f"AND ra.year='{year}'" if year else ""}
        {f"AND ra.round='{race}'" if race else ((f"AND ra.round=(SELECT MAX(round) FROM races WHERE races.year='{year}')" if year else "AND (ra.year, ra.round) IN (SELECT year, MAX(round) FROM races GROUP BY year)") if driverStanding or constructorStanding else "")}
        ORDER BY dr.surname
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    ress = json.dumps(res)
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "driverId",
            "permanentNumber",
            "driverCode",
            "givenName",
            "familyName",
            "dateOfBirth",
            "nationality",
            "url",
        ],
    )
    return df


def constructor_information(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    constructorStanding: Optional[int] = None,
    driverStanding: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain a list of all constructors within a series, year or round.
    Each constructor listed is identified by a unique constructorId which is used to
    identify the constructor throughout the API.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional):  Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        constructorStanding (Optional[int], optional): Limit results by a final
            CDC finishing position (e.g. only constructors that have finished in 3rd
            place). Defaults to None.
        driverStanding (Optional[int], optional): Limit results by a final WDC position
            (e.g. only drivers that have finished a season in 3rd place).
            Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Raises:
        ValueError: Cannot combine standings with circuit, grid, result or status qualifiers.

    Returns:
        pd.DataFrame: Pandas DataFrame with list of constructors for the given criteria.
    """
    if (driverStanding or constructorStanding) and (
        circuit or grid or result or status
    ):
        raise ValueError(
            "Cannot combine standings with circuit, grid, result or status qualifiers."
        )

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT
            constructors.constructorRef, constructors.name, constructors.nationality, constructors.url
        FROM constructors
        {", results" if year or driver or status or grid or result or circuit or fastest else ""}
        {", races" if year or circuit or driverStanding or constructorStanding else ""}
        {", driverStandings" if driverStanding or (constructorStanding and driver) else ""}
        {", constructorStandings" if constructorStanding else ""}
        {", circuits" if circuit else ""}
        {", drivers" if driver else ""}
        WHERE TRUE
        {"AND constructors.constructorId=results.constructorId" if year or driver or status or grid or result or circuit or fastest else ""}
        {"AND results.raceId=races.raceId" if year or circuit else ""}
        {f"AND races.circuitId=circuits.circuitId AND circuits.circuitRef='{circuit}'" if circuit else ""}
        {f"AND results.driverId=drivers.driverId AND drivers.driverRef='{driver}'" if driver else ""}
        {f"AND results.statusId='{status}'" if status else ""}
        {f"AND results.grid='{grid}'" if grid else ""}
        {f"AND results.rank='{fastest}'" if fastest else ""}
        {f"AND results.positionText='{result}'" if result else ""}
        {f"AND constructors.constructorRef='{constructor}'" if constructor else ""}
        {f"AND driverStandings.positionText='{driverStanding}' AND driverStandings.constructorId=constructors.constructorId" if driverStanding else ""}
        {"AND driverStandings.raceId=races.raceId" if driverStanding or (constructorStanding and driver) else ""}
        {"AND drivers.driverId=driverStandings.driverId" if (driverStanding or constructorStanding) and driver else ""}
        {f"AND constructorStandings.positionText='{constructorStanding}' AND constructorStandings.constructorId=constructors.constructorId AND constructorStandings.raceId=races.raceId" if constructorStanding else ""}
        {"AND driverStandings.constructorId=constructorStandings.constructorId" if constructorStanding and driver else ""}
        {f"AND races.year='{year}'" if year else ""}
        {f"AND races.round='{race}'" if race else ((f"AND races.round=(SELECT MAX(round) FROM races WHERE races.year='{year}')" if year else "AND (races.year, races.round) IN (SELECT year, MAX(round) FROM races GROUP BY year)") if driverStanding or constructorStanding else "")}
        ORDER BY constructors.name
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=["constructorId", "constructorName", "nationality", "url"],
    )
    return df


def circuit_information(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain a list of the circuits used within a series, year or round.
    Each circuit listed is identified by a unique circuitId which is used to identify
    the circuit throughout the API.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with circuit list for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT
            ci.circuitRef, ci.name, ci.location, ci.country, ci.lat, ci.lng, ci.url
        FROM circuits ci
        {", races ra" if year or driver or constructor or status or grid or fastest or result else ""}
        {", results re" if driver or constructor or status or grid or fastest or result else ""}
        {", drivers dr" if driver else ""}
        {", constructors co" if constructor else ""}
        WHERE TRUE
        {"AND ra.circuitId=ci.circuitId" if year or driver or constructor or status or grid or fastest or result else ""}
        {f"AND ci.circuitRef='{circuit}'" if circuit else ""}
        {"AND re.raceId=ra.raceId" if driver or constructor or status or grid or fastest or result else ""}
        {f"AND re.constructorId=co.constructorId AND co.constructorRef='{constructor}'" if constructor else ""}
        {f"AND re.driverId=dr.driverId AND dr.driverRef='{driver}'" if driver else ""}
        {f"AND re.statusId='{status}'" if status else ""}
        {f"AND re.grid='{grid}'" if grid else ""}
        {f"AND re.rank='{fastest}'" if fastest else ""}
        {f"AND re.positionText='{result}'" if result else ""}
        {f"AND ra.year='{year}'" if year else ""}
        {f"AND ra.round='{race}'" if race else ""}
        ORDER BY ci.circuitRef
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "circuitId",
            "circuitName",
            "locality",
            "country",
            "lat",
            "long",
            "url",
        ],
    )
    return df


def finishing_status(
    *,
    year: Optional[int] = None,
    race: Optional[int] = None,
    circuit: Optional[str] = None,
    constructor: Optional[str] = None,
    driver: Optional[str] = None,
    grid: Optional[int] = None,
    result: Optional[int] = None,
    fastest: Optional[int] = None,
    status: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Obtain a list of all finishing status codes used by the API.

    Args:
        year (Optional[int], optional): Season calendar year. Defaults to None.
        race (Optional[int], optional): Race round in the selected calendar year.
            Defaults to None.
        circuit (Optional[str], optional): Limit results to a specified circuit
            (e.g. monaco). Defaults to None.
        constructor (Optional[str], optional): Limit results to a specified constructor
            (e.g. renault). Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        grid (Optional[int], optional): Limit results to a specific starting grid
            position. Defaults to None.
        result (Optional[int], optional): Limit results to a specific finishing
            position. Defaults to None.
        fastest (Optional[int], optional): Limit results to a specific fastest lap rank
            (e.g. 3 means 3rd fastest lap holder). Defaults to None.
        status (Optional[int], optional): Limit results to a specific race outcome
            (e.g. 1 means finished). This is fairly useless since you cant know in
            advance what the statusIds are. Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with race status codes for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT DISTINCT st.statusId, st.status, COUNT(*)
        FROM status st
        {", races ra" if year or race or circuit else ""}
        , results re
        {", drivers dr" if driver else ""}
        {", constructors co" if constructor else ""}
        {", circuits ci" if circuit else ""}
        WHERE TRUE
        {f"AND st.statusId='{status}'" if status else ""}
        AND re.statusId=st.statusId
        {"AND re.raceId=ra.raceId" if year or race or circuit else ""}
        {f"AND re.constructorId=co.constructorId AND co.constructorRef='{constructor}'" if constructor else ""}
        {f"AND re.driverId=dr.driverId AND dr.driverRef='{driver}'" if driver else ""}
        {f"AND ra.circuitId=ci.circuitId AND ci.circuitRef='{circuit}'" if circuit else ""}
        {f"AND re.grid='{grid}'" if grid else ""}
        {f"AND re.rank='{fastest}'" if fastest else ""}
        {f"AND re.positionText='{result}'" if result else ""}
        {f"AND ra.year='{year}'" if year else ""}
        {f"AND ra.round='{race}'" if race else ""}
        GROUP BY st.statusId ORDER BY st.statusId
        {f"LIMIT {offset}, {limit}" if offset and limit else ""} 
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "statusId",
            "status",
            "count",
        ],
    )
    return df


def lap_times(
    year: int,
    race: int,
    *,
    lap: Optional[int] = None,
    driver: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Lap time data is available from the 1996 season onwards.
    Lap time queries require the season, round and lap number to be specified.

    Args:
        year (int): Season calendar year, should be from 1996 onwards.
        race (int): Race round in the selected calendar year.
        lap (Optional[int], optional): Limit results to a specific lap. Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with race laps for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT
            ra.year, ra.round, ra.name, ra.date, ra.time, ra.url, 
            ci.circuitRef, ci.name, ci.location, ci.country, ci.url, ci.lat, ci.lng, ci.alt,
            dr.driverRef,
            la.lap, la.position, la.time, la.milliseconds
        FROM lapTimes la, races ra, circuits ci, drivers dr
        WHERE ra.circuitId=ci.circuitId
            AND la.driverId=dr.driverId
            AND la.raceId=ra.raceId
            AND ra.year='{year}'
            AND ra.round='{race}'
            {f"AND la.lap='{lap}'" if lap else ""}
            {f"AND dr.driverRef='{driver}'" if driver else ""}
        ORDER BY la.lap, la.position
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "year",
            "round",
            "raceName",
            "date",
            "time",
            "url",
            "circuitId",
            "circuitName",
            "locality",
            "country",
            "circuitUrl",
            "lat",
            "long",
            "altitude",
            "driverId",
            "lap",
            "position",
            "lapTime",
            "millis",
        ],
    )
    return df


def pit_stops(
    year: int,
    race: int,
    *,
    pitstop: Optional[int] = None,
    lap: Optional[int] = None,
    driver: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Pit stop data is available from the 2012 season onwards.
    Pit stop queries require a season and a round to be specified.

    Args:
        year (int): Season calendar year, should be from 2012 onwards.
        race (int): Race round in the selected calendar year.
        pitstop (Optional[int], optional): The number of pitstop (e.g. 3 will only
            return the third pitstop for each driver). Defaults to None.
        lap (Optional[int], optional): Limit result to a single specified lap.
            Defaults to None.
        driver (Optional[str], optional): Limit results to a specific driver
            (e.g. alonso). Defaults to None.
        offset (Optional[int], optional): If specified along with limit will return
            paginated results. Defaults to None.
        limit (Optional[int], optional): If specified along with offset will return
            paginated results. Defaults to None.

    Returns:
        pd.DataFrame: Pandas DataFrame with pitstops for the given criteria.
    """

    query = textwrap.dedent(
        f"""
        SELECT
            ra.year, ra.round, ra.name, ra.date, ra.time, ra.url, 
            ci.circuitRef, ci.name, ci.location, ci.country, ci.url, ci.lat, ci.lng, ci.alt,
            dr.driverRef,
            pi.stop, pi.lap, pi.time, pi.duration
        FROM pitStops pi, races ra, circuits ci, drivers dr
        WHERE ra.circuitId=ci.circuitId
            AND pi.driverId=dr.driverId
            AND pi.raceId=ra.raceId
            AND ra.year='{year}' AND ra.round='{race}'
            {f"AND pi.stop='{pitstop}'" if pitstop else ""}
            {f"AND pi.lap='{lap}'" if lap else ""}
            {f"AND dr.driverRef='{driver}'" if driver else ""}
        ORDER BY pi.time
        {f"LIMIT {offset}, {limit}" if offset and limit else ""}
        """
    )

    cur = con.cursor()
    res = cur.execute(query).fetchall()
    cur.close()

    df = pd.DataFrame(
        res,
        columns=[
            "year",
            "round",
            "raceName",
            "date",
            "time",
            "url",
            "circuitId",
            "circuitName",
            "locality",
            "country",
            "circuitUrl",
            "lat",
            "long",
            "altitude",
            "driverId",
            "pitstop",
            "lap",
            "localTime",  # TODO: I dont like this tbh
            "pitstopDuration",
        ],
    )
    return df
