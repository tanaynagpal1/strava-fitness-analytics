"""Feature engineering — daily_master and user_profile (Cleaning Notes/07_feature_engineering.md)."""
import numpy as np
import pandas as pd

from . import config as C

SLEEP_JOIN_COLS = ["night_hours_asleep", "sleep_efficiency", "bedtime_hrs_after_6pm", "took_nap", "reliable_night"]


def build_daily_master(daily, sleep_nights, hr_daily):
    """G: daily_clean left-joined with last night's sleep, tonight's sleep and heart rate. All 757 days kept."""
    sn = sleep_nights[["user_id", "date"] + SLEEP_JOIN_COLS]
    last = sn.rename(columns={c: f"sleep_last_night_{c}" for c in SLEEP_JOIN_COLS})
    tonight = sn.assign(date=sn["date"] - pd.Timedelta(days=1)).rename(columns={c: f"sleep_tonight_{c}" for c in SLEEP_JOIN_COLS})
    hr = hr_daily.drop(columns=["hr_minutes_recorded"])
    dm = daily.merge(last, on=["user_id", "date"], how="left").merge(tonight, on=["user_id", "date"], how="left").merge(hr, on=["user_id", "date"], how="left")
    assert len(dm) == len(daily), "join duplicated days"
    return dm


def _segment(steps):
    for lo, hi, lab in C.STEP_SEGMENTS:
        if lo <= steps < hi:
            return lab
    return None


def _clock(hours_after_6pm):
    if pd.isna(hours_after_6pm):
        return None
    total = round((18 + hours_after_6pm) % 24 * 60)
    h, m = divmod(total, 60)
    return f"{h % 12 or 12}:{m:02d} {'AM' if h % 24 < 12 else 'PM'}"


def persona_of(segment, tier):
    """Q29 persona: activity level (higher = Somewhat active / Active) x engagement tier."""
    if tier == "Barely using" or pd.isna(segment):
        return "Fading Users"
    higher = segment in ("Somewhat active", "Active")
    if tier == "Consistent":
        return "Committed Movers" if higher else "Daily Strollers"
    return "On-and-Off Movers" if higher else "Slipping Starters"


def build_user_profile(daily_raw, daily, wear_log, hourly, sleep_nights, sleep_day_raw, weight_profile, hr_daily, hr_users):
    users = sorted(daily_raw["Id"].unique())
    p = pd.DataFrame({"user_id": users})

    # ---- H1 coverage
    raw = daily_raw.groupby("Id").agg(days_in_study=("date", "size"), first_date=("date", "min"), last_date=("date", "max")).rename_axis("user_id").reset_index()
    p = p.merge(raw, on="user_id")
    clean_days = daily.groupby("user_id").size().rename("clean_days")
    p = p.merge(clean_days, on="user_id", how="left").fillna({"clean_days": 0})
    p["clean_days"] = p["clean_days"].astype(int)
    p["clean_day_share"] = (p["clean_days"] / C.STUDY_DAYS).round(3)
    wl = wear_log.pivot_table(index="user_id", columns="wear_status", values="date", aggfunc="count").fillna(0)
    p["non_wear_days"] = p["user_id"].map(wl.get("not_worn", pd.Series(dtype=float))).fillna(0).astype(int)
    p["partial_days"] = p["user_id"].map(wl.get("partial", pd.Series(dtype=float))).fillna(0).astype(int)
    p["low_data_user"] = p["clean_days"] < C.MIN_PROFILE_DAYS
    end = pd.Timestamp(C.STUDY_END)
    p["stopped_early"] = p["last_date"] <= end - pd.Timedelta(days=C.STOP_EARLY_DAYS)
    p["stopped_final_week"] = (p["last_date"] < end) & ~p["stopped_early"]

    # ---- H2 activity (medians)
    g = daily.groupby("user_id")
    act = pd.DataFrame({
        "typical_steps": g["steps"].median(), "typical_active_min": g["active_min"].median(), "typical_mvpa_min": g["mvpa_min"].median(),
        "typical_distance_km": g["distance_km"].median().round(2), "typical_calories": g["calories"].median(),
        "weekly_mvpa_min": (g["mvpa_min"].mean() * 7).round(0), "goal_10k_rate": g["goal_10k_met"].mean().round(3),
        "steps_cv": (g["steps"].std() / g["steps"].mean()).round(3),
    })
    wk = daily.pivot_table(index="user_id", columns="is_weekend", values="steps", aggfunc="median")
    act["weekday_steps"] = wk.get(False); act["weekend_steps"] = wk.get(True)
    half = daily.assign(half=np.where(daily["date"] < pd.Timestamp(C.MONTH_SPLIT), 1, 2)).pivot_table(index="user_id", columns="half", values="steps", aggfunc="median")
    act["steps_1st_half"] = half.get(1); act["steps_2nd_half"] = half.get(2)
    p = p.merge(act.reset_index(), on="user_id", how="left")

    ph = hourly.groupby(["user_id", "hour"])["steps"].mean().reset_index()
    peak = ph.loc[ph.groupby("user_id")["steps"].idxmax(), ["user_id", "hour"]].rename(columns={"hour": "peak_activity_hour"})
    p = p.merge(peak, on="user_id", how="left")
    # F6: slot with the most workout hours; tie -> more total effort (intensity); still tied -> earlier slot
    wo = hourly[hourly["workout_hour"]].groupby(["user_id", "time_of_day"]).agg(n=("hour", "size"), effort=("intensity", "sum")).reset_index()
    wo["slot_order"] = wo["time_of_day"].map({lab: i for i, (lab, _, _) in enumerate(C.TIME_OF_DAY)})
    pref = (wo.sort_values(["user_id", "n", "effort", "slot_order"], ascending=[True, False, False, True])
              .groupby("user_id").head(1)[["user_id", "time_of_day"]].rename(columns={"time_of_day": "preferred_workout_time"}))
    p = p.merge(pref, on="user_id", how="left")
    p["preferred_workout_time"] = p["preferred_workout_time"].fillna("No workouts")

    # ---- H3 segments (only for users with enough clean days)
    ok = ~p["low_data_user"]
    p["activity_segment"] = p["typical_steps"].map(_segment).where(ok)
    p["meets_activity_guideline"] = (p["weekly_mvpa_min"] >= C.MVPA_GUIDELINE_WEEK).where(ok)
    ratio = p["weekend_steps"] / p["weekday_steps"]
    p["week_pattern"] = np.select([ratio > C.WEEK_PATTERN_HIGH, ratio < C.WEEK_PATTERN_LOW], ["Weekend-active", "Weekday-active"], "Steady")
    p["week_pattern"] = p["week_pattern"].where(ok & ratio.notna())
    q1, q3 = p.loc[ok, "steps_cv"].quantile([0.25, 0.75])
    p["routine_consistency"] = np.select([p["steps_cv"] < q1, p["steps_cv"] > q3], ["Very regular", "Irregular"], "Normal")
    p["routine_consistency"] = p["routine_consistency"].where(ok)
    chg = p["steps_2nd_half"] / p["steps_1st_half"] - 1
    p["activity_trend"] = np.select([chg > C.TREND_CHANGE, chg < -C.TREND_CHANGE], ["Rising", "Falling"], "Stable")
    p["activity_trend"] = p["activity_trend"].where(ok & chg.notna())

    # ---- H4 engagement
    p["engagement_tier"] = np.select([p["stopped_early"] | (p["clean_day_share"] < C.ENGAGEMENT_BARELY), p["clean_day_share"] >= C.ENGAGEMENT_CONSISTENT],
                                     ["Barely using", "Consistent"], "Irregular")
    rel = sleep_nights[sleep_nights["reliable_night"]].groupby("user_id").size()
    p["reliable_nights"] = p["user_id"].map(rel).fillna(0).astype(int)
    tracked = set(sleep_day_raw["Id"].astype(str))
    p["tracks_sleep"] = p["user_id"].isin(tracked)
    p["sleep_adoption_level"] = np.select([~p["tracks_sleep"], p["reliable_nights"] < 7, p["reliable_nights"] < 20], ["Never", "Tried", "Regular"], "Consistent")
    p["logs_weight"] = p["user_id"].isin(set(weight_profile["user_id"]))
    logged = daily[daily["logged_workout"]].groupby("user_id").size()
    p["n_logged_days"] = p["user_id"].map(logged).fillna(0).astype(int)
    p["logs_workouts"] = p["n_logged_days"] > 0
    p["features_used"] = p[["tracks_sleep", "logs_weight", "logs_workouts"]].sum(axis=1).astype(int)

    # ---- H5 sleep profile (7+ reliable nights)
    sr = sleep_nights[sleep_nights["reliable_night"]]
    sp = sr.groupby("user_id").agg(typical_sleep_hours=("night_hours_asleep", "median"), typical_sleep_efficiency=("sleep_efficiency", "median"),
                                   bed=("bedtime_hrs_after_6pm", "median"), bedtime_regularity=("bedtime_hrs_after_6pm", "std"))
    wake = sr.assign(w=pd.to_timedelta(sr["wake_time"] + ":00").dt.total_seconds() / 3600).groupby("user_id")["w"].median()
    sp["typical_wake_time"] = wake.map(lambda h: f"{int(h) % 12 or 12}:{int(round(h % 1 * 60)):02d} {'AM' if h < 12 else 'PM'}")
    nap = sleep_nights.groupby("user_id")["took_nap"].mean().rename("nap_rate")
    p = p.merge(sp.reset_index(), on="user_id", how="left").merge(nap.reset_index(), on="user_id", how="left")
    p["low_sleep_data_user"] = p["tracks_sleep"] & (p["reliable_nights"] < C.MIN_PROFILE_DAYS)
    has = p["reliable_nights"] >= C.MIN_PROFILE_DAYS
    for c in ["typical_sleep_hours", "typical_sleep_efficiency", "bed", "bedtime_regularity", "typical_wake_time"]:
        p[c] = p[c].where(has)
    p["typical_bedtime"] = p["bed"].map(_clock)
    p["bedtime_group"] = np.select([p["bed"] < C.BEDTIME_EARLY, p["bed"] > C.BEDTIME_LATE], ["Early", "Late"], "Typical")
    p["bedtime_group"] = p["bedtime_group"].where(has)
    p["restless_sleeper"] = (p["typical_sleep_efficiency"] < C.RESTLESS_EFFICIENCY).where(has)
    p = p.rename(columns={"bed": "typical_bedtime_hrs_after_6pm"})
    p["typical_sleep_hours"] = p["typical_sleep_hours"].round(2)
    p["bedtime_regularity"] = p["bedtime_regularity"].round(2)
    p["nap_rate"] = p["nap_rate"].round(3)

    # ---- H6 body & heart
    p = p.merge(weight_profile.drop(columns=["first_log_date", "last_log_date"]), on="user_id", how="left")
    hg = hr_daily.groupby("user_id").agg(hr_days=("date", "size"), typical_resting_hr=("hr_resting_est", "median"),
                                         typical_hr_minutes_above_100=("minutes_hr_above_100", "median")).reset_index()
    p = p.merge(hg, on="user_id", how="left")
    p["hr_days"] = p["hr_days"].fillna(0).astype(int)
    p["has_hr_data"] = p["user_id"].isin(set(hr_users))
    p["low_hr_data_user"] = p["has_hr_data"] & (p["hr_days"] < C.MIN_PROFILE_DAYS)       # R6
    for c in ["typical_resting_hr", "typical_hr_minutes_above_100"]:
        p[c] = p[c].where(~p["low_hr_data_user"])            # R6: no HR profile under 7 days
    p["persona"] = [persona_of(s, t) for s, t in zip(p["activity_segment"], p["engagement_tier"])]   # F8 (Q29)
    return p
