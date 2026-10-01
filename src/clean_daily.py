"""dailyActivity cleaning — problems P1–P11 (Cleaning Notes/01_dailyActivity_cleaning.md)."""
import numpy as np
import pandas as pd

from . import config as C

MINUTE_COLS = ["VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes", "SedentaryMinutes"]
EFFORT_KM_COLS = ["VeryActiveDistance", "ModeratelyActiveDistance", "LightActiveDistance"]


def movement_hours(hourly_raw):
    """P4: number of hours in the day with at least 1 step (from the hourly table)."""
    mh = (hourly_raw.assign(moved=hourly_raw["StepTotal"] > 0)
          .groupby(["Id", "date"])["moved"].sum().rename("movement_hours").reset_index())
    return mh


def _flag_days(daily_raw, mh):
    d = daily_raw.merge(mh, on=["Id", "date"], how="left")
    d["movement_hours"] = d["movement_hours"].fillna(0).astype(int)
    d["is_last_day"] = d["date"] == d.groupby("Id")["date"].transform("max")                      # P2
    d["not_worn"] = d["TotalSteps"] < C.MIN_STEPS_WORN                                             # P3
    # H8 / P7: hourly file shows no movement at all while the daily total has real steps -> broken detail, keep the day
    d["breakdown_missing"] = (d["movement_hours"] == 0) & (d["TotalSteps"] >= C.MIN_STEPS_WORN)
    d["partial"] = (d["movement_hours"] < C.MIN_MOVEMENT_HOURS) & ~d["breakdown_missing"]          # P4
    return d


def build_wear_log(daily_raw, mh):
    """P3 add-on: one row per user per calendar day, built BEFORE any removal."""
    d = _flag_days(daily_raw, mh)
    status = np.select([d["is_last_day"], d["not_worn"], d["partial"]], ["last_day", "not_worn", "partial"], default="worn")
    d = d.assign(wear_status=status)[["Id", "date", "wear_status"]]
    grid = pd.MultiIndex.from_product([sorted(daily_raw["Id"].unique()), pd.date_range(C.STUDY_START, C.STUDY_END)], names=["Id", "date"])
    wl = d.set_index(["Id", "date"]).reindex(grid).reset_index()
    wl["wear_status"] = wl["wear_status"].fillna("stopped")                                       # P10: no row = stopped
    wl = wl.rename(columns={"Id": "user_id"})
    wl["day_of_week"] = wl["date"].dt.day_name()
    wl["week_no"] = (wl["date"] - pd.Timestamp(C.STUDY_START)).dt.days // 7 + 1
    wl["is_worn"] = wl["wear_status"] == "worn"
    return wl


def clean_daily(daily_raw, mh):
    d = _flag_days(daily_raw, mh)
    n0 = len(d)
    d = d[~d["is_last_day"]]                                    # P2
    n2 = len(d)
    d = d[~d["not_worn"]]                                        # P3
    n3 = len(d)
    d = d[~d["partial"]]                                         # P4 (broken-detail days kept)
    steps = {"raw": n0, "after_P2_last_day": n2, "after_P3_not_worn": n3, "after_P4_partial": len(d)}
    d = d.copy()

    # P7: blank (not zero) the effort breakdown where the detail never arrived
    d.loc[d["breakdown_missing"], MINUTE_COLS + EFFORT_KM_COLS] = np.nan

    # P6 / P11: drop, rename, round
    d = d.drop(columns=["TrackerDistance", "SedentaryActiveDistance", "ActivityDate", "is_last_day", "not_worn", "partial"])
    d = d.rename(columns={
        "Id": "user_id", "TotalSteps": "steps", "TotalDistance": "distance_km",
        "VeryActiveMinutes": "very_active_min", "FairlyActiveMinutes": "fairly_active_min",
        "LightlyActiveMinutes": "lightly_active_min", "SedentaryMinutes": "sedentary_min_raw",
        "VeryActiveDistance": "very_active_km", "ModeratelyActiveDistance": "moderate_active_km",
        "LightActiveDistance": "light_active_km", "LoggedActivitiesDistance": "logged_km", "Calories": "calories"})
    for c in ["distance_km", "very_active_km", "moderate_active_km", "light_active_km", "logged_km"]:
        d[c] = d[c].round(2)

    # helper columns (P5, P6, P11, F2)
    d["active_min"] = d["very_active_min"] + d["fairly_active_min"] + d["lightly_active_min"]
    d["mvpa_min"] = d["very_active_min"] + d["fairly_active_min"]
    d["goal_10k_met"] = d["steps"] >= C.GOAL_STEPS
    effort_km = d[["very_active_km", "moderate_active_km", "light_active_km"]].sum(axis=1, min_count=3)
    for c, s in [("very_active_km", "share_very_km"), ("moderate_active_km", "share_moderate_km"), ("light_active_km", "share_light_km")]:
        d[s] = (d[c] / effort_km.replace(0, np.nan)).round(4)
    d["day_of_week"] = d["date"].dt.day_name()
    d["is_weekend"] = d["date"].dt.dayofweek >= 5
    d["week_no"] = (d["date"] - pd.Timestamp(C.STUDY_START)).dt.days // 7 + 1
    d["logged_workout"] = d["logged_km"] > 0
    d = d.sort_values(["user_id", "date"]).reset_index(drop=True)
    return d, steps


def add_sleep_flags(daily, sleep_nights):
    """P5 + S5/S6: sitting time is only trustworthy on days with a complete, reliable night recorded."""
    rel = sleep_nights.loc[sleep_nights["reliable_night"], ["user_id", "date"]].assign(sleep_tracked=True)
    d = daily.drop(columns=[c for c in ["sleep_tracked", "sedentary_awake_min"] if c in daily]).merge(rel, on=["user_id", "date"], how="left")
    d["sleep_tracked"] = d["sleep_tracked"].fillna(False).astype(bool)
    d["sedentary_awake_min"] = d["sedentary_min_raw"].where(d["sleep_tracked"])
    return d
