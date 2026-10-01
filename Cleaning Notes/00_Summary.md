# 00 · Phase 1 Cleaning Plan — Summary

**Project:** Strava Fitness Data Analytics · **Author:** Tanay Nagpal · **Phase:** 1 (Planning) · **Date:** 30 Sep 2026
**Status: ✅ ALL 6 FILES PLANNED — 51 problems agreed**

---

## 1 · Business problem & objective (refined from the case study to fit the data)

**Business problem.** Strava collects detailed tracker data on users' daily activity, sleep and body metrics, but has no clear view of **which kinds of users it has, how their activity and sleep habits differ, and which tracking features they actually use**. Without this, marketing and engagement campaigns stay one-size-fits-all instead of targeted by segment, timed to user behaviour, and focused on under-used features.

**Business objective.** Analyse activity, sleep and body-metric data to **segment users by activity level and tracking consistency**, profile each segment's daily/hourly activity, sleep behaviour and feature adoption, and turn the differences into **data-driven marketing recommendations** — *which segment to target, with what message, promoting which feature, at what time* — presented in a Streamlit dashboard.

**Important context.** The data is a public Fitbit tracker dataset: 33 people, 12 Apr – 12 May 2016. It has **no activity types** (no running/cycling labels) — effort levels, distance and step-free effort are used instead. Findings are directional (small sample), and correlation is never presented as cause.

---

## 2 · Files used and skipped

| Used (6 groups) | Why |
|---|---|
| dailyActivity | Main table — one row per person per day |
| hourlySteps + hourlyCalories + hourlyIntensities | Time-of-day patterns |
| sleepDay | Nightly sleep totals |
| minuteSleep | Bedtime, wake time, naps, restlessness |
| weightLogInfo | BMI profile + feature adoption |
| heartrate_seconds | Supporting evidence (effort, data quality) |

| Skipped (10 files) | Why |
|---|---|
| dailyCalories, dailySteps, dailyIntensities | 100% identical to dailyActivity |
| minuteSteps / minuteCalories / minuteIntensities (Narrow + Wide, 6 files) | Add up exactly to the hourly files; Wide = same data re-arranged |
| minuteMETsNarrow | Low priority; effort already covered by intensity |

---

## 3 · Project-wide rules (apply to every file)

| # | Rule |
|---|---|
| 1 | **Dates:** always convert with the explicit American format (month/day/year, AM/PM) — never let Python guess (Indian day/month trap) |
| 2 | **Remove only the impossible**, never the unusual — high values from real workouts stay |
| 3 | **Never invent data** — no filling missing days/hours; use **blank** (not 0) when a value is unknown |
| 4 | **Record before removing** — `wear_log` saves every removed day for the engagement page |
| 5 | **Valid day** = not the person's last day · ≥ 100 steps · movement in ≥ 10 different hours |
| 6 | **7-day rule** — per-person profiles need ≥ 7 valid days / reliable nights |
| 7 | **Medians** for "typical" values (one special day can't pull them) |
| 8 | **One table = one level of detail** — person-level items go to `user_profile` |
| 9 | **Main activity measures = steps + active minutes**; sitting time only on complete sleep nights |
| 10 | **State the sample size** on every chart that uses a subset (sleep, weight, heart rate) |
| 11 | **Neutral wording** — no health or medical labels; correlation ≠ cause |

---

## 4 · Clean outputs (what Phase 2 will produce)

| Output file | Rows | One row = | Built from |
|---|---|---|---|
| `daily_clean.csv` | **757** | person-day | dailyActivity (+ movement hours, sleep flags) |
| `wear_log.csv` | **1,023** | person × calendar day | dailyActivity (worn 757 · not worn 77 · partial 73 · last day 33 · stopped 83) |
| `hourly_clean.csv` | **17,987** | person-hour | 3 hourly files (750 valid days) |
| `sleep_nights.csv` | **410** (384 reliable) | person-night | minuteSleep + sleepDay |
| `weight_logs_clean.csv` | **67** | weight entry | weightLogInfo |
| `user_body_profile.csv` | **8** | person | weightLogInfo |
| `daily_heart_rate.csv` | **280** | person-day | heartrate_seconds |
| `user_profile.csv` | **33** | person | all of the above (built in feature engineering) |

---

## 5 · Problems per file

| File | Problems | Rows: raw → clean |
|---|---|---|
| 01 · dailyActivity | 11 (P1–P11) | 940 → 757 |
| 02 · Hourly (3 files) | 9 (H1–H9) | 22,099 → 17,987 |
| 03 · sleepDay | 9 (S1–S9) | 413 → 410 nights |
| 04 · minuteSleep | 8 (M1–M8) | 188,521 minutes → 459 sessions → 410 nights |
| 05 · weightLogInfo | 7 (W1–W7) | 67 → 67 entries + 8 profiles |
| 06 · heartrate_seconds | 7 (R1–R7) | 2,483,658 readings → 280 days |
| **Total** | **51** | |

---

## 6 · Key flags created

| Table | Flags |
|---|---|
| daily_clean | `sleep_tracked` (365 days), `breakdown_missing` (7), `logged_workout` (31), `is_weekend` |
| hourly_clean | `stepless_effort` (18 hours) |
| sleep_nights | `reliable_night` (384), `incomplete_night` (22), `capped_session` (4), `long_sleep` (10), `took_nap` |
| user_profile | `low_data_user` (2), `low_sleep_data_user` (8), `low_hr_data_user` (2), `restless_sleeper` (1), `stopped_early` (4), `stopped_final_week` (8), `logs_weight` (8), `logs_workouts` (3), `sleep_adoption_level`, `features_used`, `clean_day_share`, `non_wear_days` |

---

## 7 · How the files depend on each other

| This… | …needs this first | Why |
|---|---|---|
| daily P4 (`movement_hours`) | Hourly files joined | Hours with ≥ 1 step |
| `wear_log` | Raw dailyActivity | Must be built **before** any removal |
| daily P5 (`sleep_tracked`) | `sleep_nights` (S5, S6) | Only complete, reliable nights count (365 days) |
| Hourly H3 / H8 | `daily_clean` | Same valid days everywhere |
| Heart rate R5 | `daily_clean` | Same valid days everywhere |
| sleepDay S4 / S9 | minuteSleep sessions | Naps vs night, bedtime |
| `user_profile` | Everything | Built last |

---

## 8 · Build order for Phase 2

| Step | Action |
|---|---|
| 1 | Load all 6 sources; convert dates with explicit formats |
| 2 | Join the 3 hourly files; compute `movement_hours` per person-day |
| 3 | Build `wear_log` from the raw daily rows |
| 4 | Clean dailyActivity (P2 → P3 → P4 → P7 → P11) |
| 5 | minuteSleep → sessions → nights (naps, pieces, flags) → `sleep_nights` |
| 6 | Add sleep flags to daily (`sleep_tracked`, `sedentary_awake_min`) |
| 7 | Filter hourly to valid days → `hourly_clean` |
| 8 | Weight → `weight_logs_clean` + `user_body_profile` |
| 9 | Heart rate → `daily_heart_rate` |
| 10 | Build `user_profile`; run every "How we'll check" test |

---

## 9 · Findings already spotted during cleaning (to confirm in EDA)

- **Non-wear is concentrated:** 12 of 33 people leave the band off; strongest pattern = take it off during the day (e.g., to charge) and forget.
- **Novelty fades:** non-wear rises from 6.6% (week 1) to 9–10% (weeks 2–4); 4 clear drop-outs.
- **Peak activity time:** 5–7 PM (6 PM highest); wake ≈ 7 AM, bed ≈ 11:15 PM.
- **Step counts miss non-walking workouts:** one user ranks 16th by steps but 4th by hard-effort minutes.
- **Sleep:** typical night 7 h 13 min, 94% efficiency; 22% of reliable nights under 6 h; weekend lie-ins and recovery sleep after very active days.
- **Feature depth:** people using more optional features (sleep, weight, workout logging) tend to be more active and wear the band more.
- **Adoption gaps:** sleep tracking used consistently by ~half; weight logging by 24% (2 habitual); workout logging by 9%.
