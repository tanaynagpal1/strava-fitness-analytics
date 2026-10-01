"""weightLogInfo cleaning — problems W1–W7 (Cleaning Notes/05_weightLogInfo_cleaning.md)."""
import pandas as pd

from . import config as C


def bmi_category(b):
    for lo, hi, lab in C.BMI_CATEGORIES:
        if lo <= b < hi:
            return lab
    return None


def clean_weight(w_raw):
    w = w_raw.drop(columns=["Fat", "WeightPounds", "LogId", "Date"])     # W1, W2
    w = w.rename(columns={"Id": "user_id", "WeightKg": "weight_kg", "BMI": "bmi", "IsManualReport": "is_manual"})
    w["date"] = w["datetime"].dt.normalize()                               # W3: manual entries carry a fake 11:59:59 PM
    w["weight_kg"] = w["weight_kg"].round(1)
    w["bmi"] = w["bmi"].round(1)
    w["bmi_category"] = w["bmi"].map(bmi_category)
    return w[["user_id", "date", "weight_kg", "bmi", "bmi_category", "is_manual"]].sort_values(["user_id", "date"]).reset_index(drop=True)


def user_body_profile(w):
    """W4: one row per person — every person counts once, whatever their number of entries."""
    p = w.groupby("user_id").agg(bmi=("bmi", "median"), weight_kg=("weight_kg", "median"), n_weight_logs=("bmi", "size"),
                                 manual_share=("is_manual", "mean"), first_log_date=("date", "min"), last_log_date=("date", "max")).reset_index()
    p["bmi"] = p["bmi"].round(1)
    p["bmi_category"] = p["bmi"].map(bmi_category)
    p["weight_habit"] = p["n_weight_logs"] >= C.WEIGHT_HABIT_LOGS
    return p
