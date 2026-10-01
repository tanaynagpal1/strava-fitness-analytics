"""Every "How we'll check" test from the Phase 1 cleaning plan, run against the outputs."""
import pandas as pd


class Checker:
    def __init__(self):
        self.rows = []

    def eq(self, ref, name, actual, expected):
        ok = actual == expected
        self.rows.append((ref, name, expected, actual, ok))
        return ok

    def approx(self, ref, name, actual, expected, tol):
        ok = actual is not None and abs(actual - expected) <= tol
        self.rows.append((ref, name, f"{expected} ± {tol}", round(actual, 3) if actual is not None else None, ok))
        return ok

    def true(self, ref, name, cond, detail=""):
        self.rows.append((ref, name, "True", detail or bool(cond), bool(cond)))
        return bool(cond)

    def table(self):
        return pd.DataFrame(self.rows, columns=["ref", "check", "expected", "actual", "pass"])

    def markdown(self):
        t = self.table()
        lines = ["| Ref | Check | Expected | Actual | Result |", "|---|---|---|---|---|"]
        for r in t.itertuples():
            lines.append(f"| {r.ref} | {r.check} | {r.expected} | {r.actual} | {'✅' if r._5 else '❌'} |")
        return "\n".join(lines)


def counts(s):
    return {k: int(v) for k, v in s.value_counts(dropna=True).sort_index().items()}


def run_all(t, steps):
    """t: dict of output tables, steps: dict of row counts per cleaning step."""
    c = Checker()
    d, wl, h, sn, ss = t["daily_clean"], t["wear_log"], t["hourly_clean"], t["sleep_nights"], t["sleep_sessions"]
    w, wp, hr, up, dm = t["weight_logs_clean"], t["user_body_profile"], t["daily_heart_rate"], t["user_profile"], t["daily_master"]
    ds = steps["daily"]

    # ---------------- dailyActivity
    c.eq("P1", "raw rows", ds["raw"], 940)
    c.true("P1", "first date is Tue 12 Apr 2016", d["date"].min() == pd.Timestamp("2016-04-12") and d["date"].min().day_name() == "Tuesday")
    c.eq("P2", "rows after removing last days", ds["after_P2_last_day"], 907)
    c.eq("P2", "no 12 May rows", int((d["date"] == pd.Timestamp("2016-05-12")).sum()), 0)
    c.eq("P3", "rows after removing not-worn days", ds["after_P3_not_worn"], 830)
    c.true("P3", "minimum steps >= 100", d["steps"].min() >= 100, int(d["steps"].min()))
    c.eq("P4", "rows after removing partial days", ds["after_P4_partial"], 757)
    c.true("P4", "every day has >= 10 movement hours or broken detail", ((d["movement_hours"] >= 10) | d["breakdown_missing"]).all())
    c.eq("P4", "users kept", d["user_id"].nunique(), 33)
    c.eq("P4", "duplicate (user, date)", int(d.duplicated(["user_id", "date"]).sum()), 0)
    c.eq("P5", "sleep_tracked days", int(d["sleep_tracked"].sum()), 365)
    c.approx("P5", "median sedentary_awake_min", float(d["sedentary_awake_min"].median()), 712, 15)
    c.eq("P6", "logged-workout days", int(d["logged_workout"].sum()), 31)
    c.eq("P6", "users logging workouts", d.loc[d["logged_workout"], "user_id"].nunique(), 3)
    c.eq("P7", "breakdown_missing days", int(d["breakdown_missing"].sum()), 7)
    c.true("P7", "breakdown blank on those days", d.loc[d["breakdown_missing"], "active_min"].isna().all())
    c.eq("P7", "days with >1,000 steps but 0 active min", int(((d["steps"] > 1000) & (d["active_min"] == 0)).sum()), 0)
    c.true("P11", "dropped TrackerDistance / SedentaryActiveDistance", not {"TrackerDistance", "SedentaryActiveDistance"} & set(d.columns))
    c.true("P11", "user_id stored as text", d["user_id"].map(type).eq(str).all())
    c.eq("P3/P11", "wear_log rows (33 × 31)", len(wl), 1023)
    c.eq("P3/P11", "wear_log status counts", counts(wl["wear_status"]), {"last_day": 33, "not_worn": 77, "partial": 73, "stopped": 83, "worn": 757})

    # ---------------- hourly
    c.eq("H1", "hourly raw rows joined", steps["hourly_raw"], 22099)
    c.eq("H3", "hourly clean rows", len(h), 17987)
    c.eq("H3", "valid days in hourly", h.groupby(["user_id", "date"]).ngroups, 750)
    c.eq("H9", "stepless-effort hours", int(h["stepless_effort"].sum()), 18)
    c.eq("H9", "…of which user …63200", int(h.loc[h["stepless_effort"], "user_id"].eq("8378563200").sum()), 16)

    # ---------------- sleep
    c.eq("S1", "sleep nights (wake dates)", len(sn), 410)
    c.eq("S1", "sleep users", sn["user_id"].nunique(), 24)
    c.eq("M1", "sessions", len(ss), 459)
    c.eq("S4", "session types", counts(ss["session_type"]), {"main_sleep": 410, "nap": 31, "night_piece": 18})
    inbed = ss.groupby(["user_id", "wake_date"])["minutes_in_bed"].sum().reset_index().rename(columns={"wake_date": "date"})
    m = inbed.merge(sn[["user_id", "date", "total_in_bed_incl_naps"]], on=["user_id", "date"])
    c.approx("S3/S4", "night + nap time in bed = sleepDay total (share)", float((m["minutes_in_bed"] == m["total_in_bed_incl_naps"]).mean()), 1.0, 0.0)
    c.eq("S5", "incomplete nights", int(sn["incomplete_night"].sum()), 22)
    c.eq("S6", "capped-session nights", int(sn["capped_session"].sum()), 4)
    c.eq("S6", "long-sleep nights", int(sn["long_sleep"].sum()), 10)
    c.eq("S5/S6", "reliable nights", int(sn["reliable_night"].sum()), 384)
    rel = sn[sn["reliable_night"]]
    c.approx("S9", "median night sleep (min)", float(rel["night_minutes_asleep"].median()), 433, 1)
    c.approx("S9", "median sleep efficiency", float(rel["sleep_efficiency"].median()), 0.943, 0.002)
    c.eq("S9", "sleep categories", counts(rel["sleep_category"]), {"6–7 h": 78, "7–9 h": 189, "< 6 h": 86, "> 9 h": 31})

    # ---------------- weight
    c.eq("W4", "weight entries / users", (len(w), w["user_id"].nunique()), (67, 8))
    c.eq("W7", "BMI categories (per person)", counts(wp["bmi_category"]), {"Normal": 3, "Obese": 1, "Overweight": 4})
    c.eq("W7", "weight habit users", int(wp["weight_habit"].sum()), 2)

    # ---------------- heart rate
    hs = steps["heart"]
    c.eq("R1", "HR user-days", hs["user_days"], 334)
    c.eq("R3", "days with >= 10 h readings", hs["after_R3_coverage"], 284)
    c.eq("R5", "valid HR days", len(hr), 280)
    c.eq("R5", "HR users with valid days", hr["user_id"].nunique(), 13)

    # ---------------- features
    c.eq("G", "daily_master rows", len(dm), 757)
    c.eq("H1", "user_profile rows", len(up), 33)
    c.eq("P9", "low_data_user", int(up["low_data_user"].sum()), 2)
    c.eq("F3", "activity segments", counts(up["activity_segment"]), {"Active": 11, "Low active": 5, "Sedentary": 5, "Somewhat active": 10})
    c.eq("F4", "meet activity guideline", int(up["meets_activity_guideline"].eq(True).sum()), 18)
    c.eq("F5", "engagement tiers", counts(up["engagement_tier"]), {"Barely using": 6, "Consistent": 20, "Irregular": 7})
    c.eq("P10", "stopped early / final week", (int(up["stopped_early"].sum()), int(up["stopped_final_week"].sum())), (4, 8))
    c.eq("F6", "week pattern", counts(up["week_pattern"]), {"Steady": 4, "Weekday-active": 11, "Weekend-active": 16})
    c.eq("F6", "activity trend", counts(up["activity_trend"]), {"Falling": 12, "Rising": 7, "Stable": 12})
    c.eq("F6", "preferred workout time", counts(up["preferred_workout_time"]), {"Afternoon": 9, "Evening": 8, "Morning": 13, "No workouts": 3})
    c.eq("S8", "sleep adoption", counts(up["sleep_adoption_level"]), {"Consistent": 12, "Never": 9, "Regular": 4, "Tried": 8})
    c.eq("S8", "low_sleep_data_user", int(up["low_sleep_data_user"].sum()), 8)
    c.eq("F7", "bedtime groups", counts(up["bedtime_group"]), {"Early": 4, "Late": 4, "Typical": 8})
    c.eq("S7", "restless sleeper", int(up["restless_sleeper"].eq(True).sum()), 1)
    c.eq("W6", "features used 0/1/2/3", counts(up["features_used"]), {0: 7, 1: 18, 2: 7, 3: 1})
    c.eq("R6", "low_hr_data_user", int(up["low_hr_data_user"].sum()), 2)
    c.eq("R6", "HR profiles (people with typical resting HR)", int(up["typical_resting_hr"].notna().sum()), 12)
    c.eq("F8", "personas", counts(up["persona"]), {"Committed Movers": 17, "Daily Strollers": 3, "Fading Users": 6, "On-and-Off Movers": 2, "Slipping Starters": 5})
    return c