"""Sleep cleaning — sleepDay S1–S9 and minuteSleep M1–M8 (Cleaning Notes/03 and 04).

Output: one row per user per wake-up date (`sleep_nights`), built from the minute
detail, with sleepDay's original totals kept for reference.
"""
import numpy as np
import pandas as pd

from . import config as C

STATE = {1: "asleep", 2: "restless", 3: "awake"}          # M3


def clean_sleep_day(sd_raw):
    sd = sd_raw.drop_duplicates()                           # S1: 3 exact copies
    sd = sd.rename(columns={"Id": "user_id", "TotalSleepRecords": "sleep_records",
                            "TotalMinutesAsleep": "total_asleep_incl_naps", "TotalTimeInBed": "total_in_bed_incl_naps"})
    return sd[["user_id", "date", "sleep_records", "total_asleep_incl_naps", "total_in_bed_incl_naps"]].reset_index(drop=True)


def clean_minute_sleep(ms_raw):
    ms = ms_raw.drop_duplicates(subset=["Id", "date", "value", "logId"])     # M1: one night copied twice
    ms = ms.rename(columns={"Id": "user_id", "logId": "session_id"})
    ms["minute"] = ms["datetime"].dt.floor("min")                              # M2: :30 seconds -> whole minute
    ms["sleep_state"] = ms["value"].map(STATE)                                 # M3
    return ms[["user_id", "session_id", "minute", "value", "sleep_state"]]


def sessions(ms):
    """M4–M7: one row per sleep session, labelled main / night_piece / nap."""
    s = ms.groupby(["user_id", "session_id"]).agg(
        start=("minute", "min"), end=("minute", "max"), minutes_in_bed=("value", "size"),
        minutes_asleep=("value", lambda v: int((v == 1).sum())),
        restless_minutes=("value", lambda v: int((v == 2).sum())),
        awake_minutes=("value", lambda v: int((v == 3).sum()))).reset_index()
    s["wake_date"] = s["end"].dt.normalize()                                   # M4 / S3
    s["rank"] = s.groupby(["user_id", "wake_date"])["minutes_in_bed"].rank(ascending=False, method="first")
    main = s.loc[s["rank"] == 1, ["user_id", "wake_date", "start", "end"]].rename(columns={"start": "m_start", "end": "m_end"})
    s = s.merge(main, on=["user_id", "wake_date"])
    gap_after = (s["start"] - s["m_end"]).dt.total_seconds() / 3600
    gap_before = (s["m_start"] - s["end"]).dt.total_seconds() / 3600
    near = gap_after.between(-0.1, C.NAP_GAP_HOURS) | gap_before.between(-0.1, C.NAP_GAP_HOURS)
    s["session_type"] = np.where(s["rank"] == 1, "main_sleep", np.where(near, "night_piece", "nap"))   # M5 / S4
    s["capped_session"] = s["minutes_in_bed"] == C.CAPPED_SESSION_MIN                                  # M7 / S6
    return s.drop(columns=["rank", "m_start", "m_end"])


def build_sleep_nights(sd_raw, ms_raw):
    sd = clean_sleep_day(sd_raw)
    ms = clean_minute_sleep(ms_raw)
    s = sessions(ms)
    night = s[s["session_type"] != "nap"]
    n = night.groupby(["user_id", "wake_date"]).agg(
        night_minutes_asleep=("minutes_asleep", "sum"), night_minutes_in_bed=("minutes_in_bed", "sum"),
        restless_minutes=("restless_minutes", "sum"), awake_minutes=("awake_minutes", "sum"),
        night_pieces=("session_id", "size"), bed_start=("start", "min"), last_minute=("end", "max"),
        capped_session=("capped_session", "any")).reset_index()
    naps = s[s["session_type"] == "nap"].groupby(["user_id", "wake_date"])["minutes_asleep"].sum().rename("nap_minutes").reset_index()
    n = n.merge(naps, on=["user_id", "wake_date"], how="left")
    n["nap_minutes"] = n["nap_minutes"].fillna(0)

    # S5: under 3 h = incomplete night; a daytime-only "night" is really a nap (kind A)
    n["incomplete_night"] = n["night_minutes_asleep"] < C.MIN_NIGHT_ASLEEP
    kind_a = n["incomplete_night"] & n["bed_start"].dt.hour.isin(list(C.DAYTIME_START_HOURS))
    n.loc[kind_a, "nap_minutes"] = n.loc[kind_a, "nap_minutes"] + n.loc[kind_a, "night_minutes_asleep"]
    num_cols = ["night_minutes_asleep", "night_minutes_in_bed", "restless_minutes", "awake_minutes", "night_pieces"]
    n[num_cols] = n[num_cols].astype(float)
    n.loc[kind_a, num_cols] = np.nan                     # no night recorded that date
    n.loc[kind_a, ["bed_start", "last_minute"]] = pd.NaT
    n["took_nap"] = n["nap_minutes"] > 0
    n["reliable_night"] = ~n["incomplete_night"] & ~n["capped_session"]                               # S5 + S6
    n["long_sleep"] = n["reliable_night"] & (n["night_minutes_asleep"] > C.LONG_SLEEP_MIN)            # S6

    n["night_hours_asleep"] = (n["night_minutes_asleep"] / 60).round(2)
    n["sleep_efficiency"] = (n["night_minutes_asleep"] / n["night_minutes_in_bed"]).round(4)          # S7
    n["minutes_awake_in_bed"] = n["night_minutes_in_bed"] - n["night_minutes_asleep"]
    n["bedtime"] = n["bed_start"].dt.strftime("%H:%M")
    n["wake_time"] = (n["last_minute"] + pd.Timedelta(minutes=1)).dt.strftime("%H:%M")
    n["bedtime_hrs_after_6pm"] = ((n["bed_start"].dt.hour + n["bed_start"].dt.minute / 60 - 18) % 24).round(2)
    cats = pd.cut(n["night_minutes_asleep"], [lo for lo, _, _ in C.SLEEP_CATEGORIES] + [C.SLEEP_CATEGORIES[-1][1]],
                  labels=[lab for _, _, lab in C.SLEEP_CATEGORIES], right=False)
    n["sleep_category"] = cats.astype("object").where(n["reliable_night"])                          # reliable nights only
    n = n.rename(columns={"wake_date": "date"})
    n["day_of_week"] = n["date"].dt.day_name()
    n["is_weekend_morning"] = n["date"].dt.dayofweek >= 5
    n = n.merge(sd, on=["user_id", "date"], how="left")                                                # reference totals
    n = n.drop(columns=["bed_start", "last_minute"])
    return n.sort_values(["user_id", "date"]).reset_index(drop=True), s
