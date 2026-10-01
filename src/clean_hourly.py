"""Hourly cleaning — problems H1–H9 (Cleaning Notes/02_hourly_cleaning.md)."""
import pandas as pd

from . import config as C


def time_of_day(hour):
    for label, lo, hi in C.TIME_OF_DAY:
        if lo <= hour <= hi:
            return label
    return None


def clean_hourly(hourly_raw, daily_clean):
    h = hourly_raw.rename(columns={"Id": "user_id", "StepTotal": "steps", "Calories": "calories", "TotalIntensity": "intensity"})
    h = h.drop(columns=["ActivityHour", "AverageIntensity"])            # H7: AverageIntensity = intensity / 60
    # H3 + H8: only hours of valid days, and not the 7 days whose hourly detail is broken
    valid = daily_clean.loc[~daily_clean["breakdown_missing"], ["user_id", "date"]]
    h = h.merge(valid, on=["user_id", "date"], how="inner")
    h["hour"] = h["datetime"].dt.hour
    h["day_of_week"] = h["datetime"].dt.day_name()
    h["is_weekend"] = h["datetime"].dt.dayofweek >= 5
    h["time_of_day"] = h["hour"].map(time_of_day)
    h["stepless_effort"] = (h["steps"] == 0) & (h["intensity"] >= C.STEPLESS_MIN_INTENSITY)     # H9
    h["workout_hour"] = h["intensity"] >= C.WORKOUT_HOUR_INTENSITY                               # F2
    return h.sort_values(["user_id", "datetime"]).reset_index(drop=True)
