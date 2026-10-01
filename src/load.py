"""Load the 8 raw CSV files we use (6 sources) with explicit date formats."""
import pandas as pd

from . import config as C


def _read(key, **kw):
    df = pd.read_csv(C.RAW_DIR / C.RAW_FILES[key], **kw)
    df["Id"] = df["Id"].astype(str)          # P11: user id is a name tag, not a number
    return df


def load_daily():
    df = _read("daily")
    df["date"] = pd.to_datetime(df["ActivityDate"], format=C.DATE_FMT)   # P1
    return df


def load_hourly():
    """H1: the three hourly files share exactly the same (user, hour) rows -> one table."""
    steps = _read("hourly_steps")
    cal = _read("hourly_calories")
    inten = _read("hourly_intensities")
    df = steps.merge(cal, on=["Id", "ActivityHour"], how="inner").merge(inten, on=["Id", "ActivityHour"], how="inner")
    assert len(df) == len(steps) == len(cal) == len(inten), "hourly files do not line up"
    df["datetime"] = pd.to_datetime(df["ActivityHour"], format=C.DATETIME_FMT)   # H2
    df["date"] = df["datetime"].dt.normalize()
    return df


def load_sleep_day():
    df = _read("sleep_day")
    df["date"] = pd.to_datetime(df["SleepDay"], format=C.DATETIME_FMT).dt.normalize()   # S2
    return df


def load_minute_sleep():
    df = _read("minute_sleep")
    df["datetime"] = pd.to_datetime(df["date"], format=C.DATETIME_FMT)   # M2
    return df


def load_weight():
    df = _read("weight")
    df["datetime"] = pd.to_datetime(df["Date"], format=C.DATETIME_FMT)   # W3
    return df


def load_heartrate():
    df = _read("heartrate")
    df["datetime"] = pd.to_datetime(df["Time"], format=C.DATETIME_FMT)   # R2 (explicit format = much faster)
    return df
