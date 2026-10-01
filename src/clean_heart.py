"""heartrate_seconds cleaning — problems R1–R7 (Cleaning Notes/06_heartrate_seconds_cleaning.md).

2.5 million 5-second readings -> one row per user per valid day.
"""
import pandas as pd

from . import config as C


def daily_heart_rate(hr_raw, daily_clean):
    hr = hr_raw.rename(columns={"Id": "user_id", "Value": "heart_rate"})
    hr["date"] = hr["datetime"].dt.normalize()
    hr["minute"] = hr["datetime"].dt.floor("min")
    per_min = hr.groupby(["user_id", "date", "minute"])["heart_rate"].mean().reset_index()
    minutes = per_min.groupby(["user_id", "date"]).agg(
        hr_minutes_recorded=("minute", "size"),
        minutes_hr_above_100=("heart_rate", lambda v: int((v > 100).sum()))).reset_index()
    # R4: percentiles, never min / max — a few seconds of spikes cannot move them
    summ = hr.groupby(["user_id", "date"])["heart_rate"].agg(
        hr_avg="mean", hr_resting_est=lambda v: v.quantile(0.05), hr_peak=lambda v: v.quantile(0.99)).reset_index()
    d = summ.merge(minutes, on=["user_id", "date"])
    n_all = len(d)
    d = d[d["hr_minutes_recorded"] >= C.HR_MIN_MINUTES]                                   # R3
    n_cov = len(d)
    d = d.merge(daily_clean[["user_id", "date"]], on=["user_id", "date"], how="inner")     # R5
    for c in ["hr_avg", "hr_resting_est", "hr_peak"]:
        d[c] = d[c].round(1)
    steps = {"user_days": n_all, "after_R3_coverage": n_cov, "after_R5_valid_days": len(d)}
    return d.sort_values(["user_id", "date"]).reset_index(drop=True), steps
