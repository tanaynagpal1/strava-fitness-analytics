# 06 · heartrate_seconds — Cleaning Notes

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning) · **Role:** Optional supporting evidence (effort & fitness) · **Status: ✅ ALL 7 PROBLEMS AGREED — plan complete**

> Running log of problems and solutions. This is the biggest file; we **summarise it to one row per person per day** and never use the raw readings in the dashboard.

---

## File at a glance

| Item | Value |
|---|---|
| What it is | Heart beats per minute, recorded every ~5 seconds |
| Size | 2,483,658 rows × 3 columns (~90 MB) |
| People | **14 of 33** |
| Time range | 12 Apr 2016 → 12 May 2016 16:20 |
| Blanks / duplicates | None / None |
| Value range | 36 – 203 bpm (median 73) |

### Columns

| Keep (renamed) | |
|---|---|
| Id → `user_id` (text) · Time → `datetime` · Value → `heart_rate` | All 3 needed |

---

## Problem summary

| # | Problem | Solution in one line | Status |
|---|---|---|---|
| R1 | Too big and too detailed | Summarise to one row per person per day (`daily_heart_rate`) | ✅ Agreed |
| R2 | Date-time stored as text | Explicit format (also makes loading much faster) | ✅ Follows P1 |
| R3 | Uneven coverage — band off for hours | Keep only days with ≥ 10 hours (600 min) of readings | ✅ Agreed |
| R4 | Extreme readings (> 200, < 40) | Nothing impossible → keep; use percentiles (5th / 99th) instead of min / max | ✅ Agreed |
| R5 | Days that are invalid in dailyActivity | Keep only days in `daily_clean` | ✅ Follows P2–P4 |
| R6 | People with little heart-rate data | Flag `low_hr_data_user` (< 7 valid days) | ✅ Agreed |
| R7 | What can we honestly claim? | Use as sanity check + effort detail; **don't** claim "active → lower resting HR" | ✅ Agreed |

**Expected result:** 334 person-days → **280 valid days**, 13 people (12 with HR profiles).

---

## R1 · Too big and too detailed — ✅ Agreed

**Why it matters** 2.5 million rows would make a Streamlit dashboard very slow, and nobody needs 5-second detail for a marketing decision.

**Solution** Summarise to one row per person per day (`daily_heart_rate.csv`):

| Column | How | Meaning |
|---|---|---|
| `hr_avg` | mean | Typical heart rate that day |
| `hr_resting_est` | 5th percentile | Stand-in for resting heart rate |
| `hr_peak` | 99th percentile | Hardest effort that day (robust — R4) |
| `minutes_hr_above_100` | minutes whose average HR > 100 | Time in elevated effort |
| `hr_minutes_recorded` | minutes with any reading | Coverage (R3) |

**Check of the resting estimate:** median 5th percentile = **59 bpm**; median heart rate **during recorded sleep** (11 people) = **60.8 bpm** → the estimate matches real resting heart rate well.

Result: 334 rows instead of 2.5 million → ~280 after R3/R5.

---

## R2 · Date-time stored as text — ✅ Follows P1

Explicit month/day/year hh:mm:ss AM/PM. For 2.5 M rows, giving the format also makes loading **much** faster than letting Python guess.

---

## R3 · Uneven coverage — ✅ Agreed

**Evidence**
- Readings usually every 5 s (90% within 15 s), but **612 gaps > 10 minutes** (band off).
- Minutes with readings per person-day: median 974 (~16 h); **50 of 334** days have < 10 h; one has 4 minutes.
- **2026352035** has 4 days of readings and **none** reaches 10 hours → drops out entirely.

**Why it matters** A day with 2 hours of readings (e.g., only a workout) gives a misleading daily average.

**Solution** Keep only days with `hr_minutes_recorded ≥ 600` (same 10-hour idea as P4) → **284** days.

---

## R4 · Extreme readings — ✅ Agreed

**Evidence**
- **> 200 bpm:** 13 readings, all user 2022484408 on 21 Apr at 4:31 PM. Heart rate goes 92 → 200 in 5 s, stays 180–203 for ~12 minutes, then slowly recovers (154 → 131 → 122). **Steps = 0** in those minutes, but the hourly effort that hour is high (intensity 97 with only 506 steps) — the same "effort without steps" pattern as hourly H9 (e.g., a bike). ⚠️ **Correction:** earlier notes called this "probably a sensor glitch". It's **uncertain**: the instant jump looks like a glitch, the slow recovery looks real. 203 bpm is not impossible for a young adult.
- **< 40 bpm:** 23 readings across 3 users, mostly 2–7 AM during sleep (possible for fit people); a few mid-afternoon.
- Together: 36 of 2.48 million readings (0.001%).
- Daily max is > 30 bpm above the 99th percentile on 41 days → single spikes are common; max/min are unreliable.

**Solution**
- **Keep** all readings (nothing impossible; can't prove the 21 Apr episode is fake).
- Use **percentiles** for daily summaries: 5th for resting, 99th for peak — a few seconds of spikes can't move them.
- Note 21 Apr (2022484408) as a "check this" day if it appears in a top-peaks chart.

---

## R5 · Invalid days — ✅ Follows P2–P4

Keep only (user, date) pairs in `daily_clean` → **280** days (284 with coverage ∩ clean daily).

---

## R6 · People with little heart-rate data — ✅ Agreed

**Evidence — valid days per person (after R3 + R5)**

| Person | Valid days |
|---|---|
| 2026352035 | **0** (dropped by R3) |
| 6775888955 | **3** |
| 4020332650 | 8 |
| Others (11) | 16 – 30 |

**Solution** Flag `low_hr_data_user` (< 7 valid days: 2026352035, 6775888955). Per-person HR profiles → **12 people**; day-level charts keep all 280 days. Every HR chart states "n = 12–13 users".

---

## R7 · What can we honestly claim? — ✅ Agreed

**Evidence (280 valid days)**
- ✅ **Sanity check passes:** very-active minutes vs minutes with HR > 100 → correlation **0.5**; steps vs average HR → **0.44**. The band's effort data and heart data agree.
- ❌ **"More active people have a lower resting heart rate" is NOT supported here:** across the 13 people, resting estimate vs typical steps → correlation **+0.22** (wrong direction, and 13 people is too few anyway). E.g., the lowest resting HR (5577150313: 48.5) has average steps; 7007744171 has high steps and the highest resting HR (74).

**Solution — how the file is used**
1. **Data-quality proof** in the EDA: "effort minutes line up with heart rate" (builds trust in the activity data).
2. **Effort detail** on the dashboard: minutes in elevated heart rate per day, for the 12 people.
3. **No** fitness claims about resting heart rate vs activity.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | R2 follows P1; R5 follows P2–P4 |
| 2026-09-30 | R1 agreed — summarise to `daily_heart_rate.csv` (avg, 5th pct resting, 99th pct peak, minutes > 100, coverage) |
| 2026-09-30 | R3 agreed — keep days with ≥ 600 minutes of readings |
| 2026-09-30 | R4 agreed — keep all readings; 21 Apr episode (2022484408) uncertain, marked 'check this'; daily summaries use 5th / 99th percentiles, never min / max |
| 2026-09-30 | R6 agreed — `low_hr_data_user` (< 7 valid days: 2026352035, 6775888955); HR profiles for 12 people |
| 2026-09-30 | R7 agreed — HR used as data-quality proof + effort detail; no resting-HR-vs-activity claims |
| 2026-10-01 | Phase 2 fix — R6 now blanks typical HR values for low_hr_data_user (6775888955 had values from 3 days); new check "HR profiles = 12" → 62/62 |