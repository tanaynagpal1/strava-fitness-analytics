# 07 · Feature Engineering — New Columns, Calculated Fields & Dimensions

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning, step 1.5) · **Status:** ✅ Agreed (F1–F7)

> Every new column we will create, grouped by table: what it is, how it's calculated, and **why** we need it.
> Columns already decided during cleaning are marked *(decided)*. New proposals that need agreement are marked **NEW**.

---

## How to read this — three kinds of columns

| Kind | Simple meaning | Example | Used for |
|---|---|---|---|
| **Dimension** | A **label** you group or filter by (answers "by what?") | `day_of_week`, `activity_segment` | Slicers, chart axes, colours |
| **Measure** | A **number** you add up / average (answers "how much?") | `active_min`, `sleep_efficiency` | KPI cards, chart values |
| **Flag** | A **Yes/No** switch | `sleep_tracked`, `reliable_night` | Filtering the right rows |

---

## Tables at a glance

| Table | Level | Rows | New columns |
|---|---|---|---|
| A · Shared time dimensions | used in every table | — | 7 |
| B · `daily_clean` | person-day | 757 | 12 |
| C · `hourly_clean` | person-hour | 17,987 | 6 |
| D · `sleep_nights` | person-night | 410 | 18 |
| E · `daily_heart_rate` | person-day | 280 | 5 |
| F · `wear_log` | person × calendar day | 1,023 | 3 |
| G · `daily_master` (joined view) | person-day | 757 | joins B + D + E |
| H · `user_profile` | person | 33 | ~45 |

---

## A · Shared time dimensions (same definition everywhere)

| Column | Kind | How | Why |
|---|---|---|---|
| `user_id` | Dimension | Id as **text** *(decided)* | Group by person; nobody averages IDs |
| `date` | Dimension | Real date *(decided)* | Joins between tables |
| `day_of_week` | Dimension | Mon … Sun from `date` *(decided)* | Weekday patterns |
| `is_weekend` | Dimension / Flag | Sat or Sun *(decided)* | Weekday vs weekend comparison |
| `week_no` | Dimension | 1–5 counted from 12 Apr *(decided)* | Trends over the month (P10) |
| `hour` | Dimension | 0–23 (hourly & HR only) *(decided)* | Time-of-day patterns |
| **`time_of_day`** **NEW** | Dimension | Night 0–4 · Morning 5–11 · Afternoon 12–16 · Evening 17–21 · Late 22–23 | Easier to read than 24 bars; maps directly to notification slots. Morning starts at **5 AM** so early workouts (e.g., the 5 AM swimmer, H9) count as morning |

---

## B · `daily_clean` — one row per person per day (757)

| Column | Kind | How | Why |
|---|---|---|---|
| `active_min` | Measure | very + fairly + lightly active min *(decided P5)* | **Main activity measure** |
| **`mvpa_min`** **NEW** | Measure | very + fairly active min ("moderate-to-vigorous") | The WHO exercise guideline counts only this kind of effort (150 min/week) |
| **`goal_10k_met`** **NEW** | Flag | steps ≥ 10,000 | The best-known daily goal; met on **40%** of days → goal-completion KPI |
| `movement_hours` | Measure | hours with ≥ 1 step *(decided P4)* | Valid-day rule; also a "how long were they up and moving" measure |
| `sedentary_awake_min` | Measure | sitting min, sleep-tracked days only *(decided P5)* | Safe sitting-time measure |
| **`share_very_km`, `share_moderate_km`, `share_light_km`** **NEW** | Measure | effort-level km ÷ sum of effort-level km | How distance splits by effort (P7: shares only, never totals) |
| `sleep_tracked` | Flag | complete reliable night on this date *(decided P5/S5/S6)* | Filter for sitting-time analysis (365 days) |
| `breakdown_missing` | Flag | 7 days *(decided P7)* | Averages skip their blank breakdown |
| `logged_workout` | Flag | logged_km > 0 *(decided P6)* | Workout-logging engagement |

---

## C · `hourly_clean` — one row per person per hour (17,987)

| Column | Kind | How | Why |
|---|---|---|---|
| `date`, `hour`, `day_of_week`, `is_weekend` | Dimension | from `datetime` *(decided H7)* | Day × hour heatmap |
| `time_of_day` **NEW** | Dimension | see A | Notification-slot charts |
| `stepless_effort` | Flag | steps = 0 and intensity ≥ 30 *(decided H9)* | Non-walking workouts |
| **`workout_hour`** **NEW** | Flag | intensity ≥ 60 (i.e., on average "fairly active" or harder for the whole hour) | Finds **when** each person exercises → preferred workout time (H) |

---

## D · `sleep_nights` — one row per person per wake-up date (410)

All decided in sleepDay S4–S9; listed here for completeness.

| Column | Kind | How | Why |
|---|---|---|---|
| `night_minutes_asleep`, `night_hours_asleep`, `night_minutes_in_bed` | Measure | main sleep + broken-night pieces | Real night sleep (no naps) |
| `sleep_efficiency` | Measure | asleep ÷ in bed | Sleep quality |
| `minutes_awake_in_bed`, `restless_minutes`, `awake_minutes` | Measure | from minute states | Quality detail |
| `night_pieces` | Measure | number of night sessions | Broken vs unbroken nights |
| `bedtime`, `wake_time` | Dimension | clock time | Timing |
| `bedtime_hrs_after_6pm` | Measure | hours after 6 PM | Lets bedtimes average correctly across midnight |
| `nap_minutes` / `took_nap` | Measure / Flag | naps that day | Napping behaviour |
| `sleep_category` | Dimension | < 6 h · 6–7 h · 7–9 h · > 9 h | Recommended-sleep share |
| `reliable_night`, `incomplete_night`, `capped_session`, `long_sleep` | Flag | S5, S6 | Filtering |
| `is_weekend_morning` | Flag | wake date is Sat/Sun | Weekend lie-ins |

---

## E · `daily_heart_rate` — one row per person per day (280)

All decided in R1.

| Column | Kind | How | Why |
|---|---|---|---|
| `hr_avg` | Measure | mean | Typical HR |
| `hr_resting_est` | Measure | 5th percentile | Resting HR (≈ HR during sleep) |
| `hr_peak` | Measure | 99th percentile | Hardest effort, spike-proof |
| `minutes_hr_above_100` | Measure | minutes with avg HR > 100 | Time in elevated effort |
| `hr_minutes_recorded` | Measure | coverage | Valid-day rule |

---

## F · `wear_log` — one row per person per calendar day (1,023)

| Column | Kind | How | Why |
|---|---|---|---|
| `wear_status` | Dimension | worn · not_worn · partial · last_day · stopped *(decided P3/P11)* | Engagement calendar |
| `day_of_week`, `week_no` | Dimension | from date | Non-wear by weekday / week |
| **`is_worn`** **NEW** | Flag | status = worn | Simple wear-rate % (share of Yes) |

---

## G · `daily_master` — joined view for analysis (757)

Not a new file of new calculations — `daily_clean` **left-joined** with:

| Joined from | Columns (prefixed) | Join key | Why |
|---|---|---|---|
| `sleep_nights` (same date) | `sleep_last_night_*` (hours, efficiency, bedtime…) | user + date | "Last night's sleep → today's activity" (S3) |
| `sleep_nights` (next date) | `sleep_tonight_*` | user + date + 1 | "Today's activity → tonight's sleep" (S3) |
| `daily_heart_rate` | `hr_*` | user + date | Effort detail, data-quality check |

Left join → all 757 days kept; blanks = "not tracked".

---

## H · `user_profile` — one row per person (33)

The most important table for **segmentation and marketing**. All "typical" values are **medians** (P8).

### H1 · Data-quality / coverage

| Column | Kind | How | Why |
|---|---|---|---|
| `days_in_study`, `last_date` | Measure / Dim | from raw daily *(decided P10)* | Drop-out analysis |
| `clean_days`, `clean_day_share` | Measure | clean days, ÷ 31 *(decided P9)* | Data reliability + engagement |
| `non_wear_days` | Measure | from wear_log *(decided P3)* | Engagement signal |
| `low_data_user`, `low_sleep_data_user`, `low_hr_data_user` | Flag | < 7 valid days/nights *(decided)* | Exclude from per-person profiles |

### H2 · Activity (medians over clean days)

| Column | Kind | Why |
|---|---|---|
| `typical_steps`, `typical_active_min`, `typical_mvpa_min`, `typical_distance_km`, `typical_calories` | Measure | Each person's normal day |
| **`weekly_mvpa_min`** **NEW** — average `mvpa_min` × 7 | Measure | Compare with the WHO 150-min/week guideline |
| **`goal_10k_rate`** **NEW** — share of days with 10k+ steps | Measure | Goal-completion behaviour |

### H3 · Segments (the core of the marketing analysis)

| Column | Kind | How | Result (31 people with ≥ 7 clean days) | Why |
|---|---|---|---|---|
| **`activity_segment`** **NEW** | Dimension | Typical steps: < 5,000 **Sedentary** · 5,000–7,499 **Low active** · 7,500–9,999 **Somewhat active** · 10,000+ **Active** (standard step-based categories) | 5 · 5 · 10 · 11 | Main segmentation; easy to explain |
| **`meets_activity_guideline`** **NEW** | Flag | `weekly_mvpa_min` ≥ 150 | 18 Yes / 13 No | Captures workouts steps miss (H9); median = 243 min/week |
| **`week_pattern`** **NEW** | Dimension | weekend ÷ weekday typical steps: > 1.1 **Weekend-active** · < 0.9 **Weekday-active** · else **Steady** | 16 · 11 · 4 | Weekday vs weekend campaign timing |
| **`routine_consistency`** **NEW** | Dimension | day-to-day variation of steps (std ÷ mean): < 0.28 **Very regular** · 0.28–0.41 **Normal** · > 0.41 **Irregular** (group quartiles) | ~¼ · ½ · ¼ | Irregular people need habit-building nudges |
| **`activity_trend`** **NEW** | Dimension | typical steps 2nd half of month vs 1st half: > +10% **Rising** · < −10% **Falling** · else **Stable** | 7 · 12 · 12 | **Falling** = early churn-risk signal |
| **`preferred_workout_time`** **NEW** | Dimension | time-of-day with the most `workout_hour`s: Morning / Afternoon / Evening / Late / None | 13 · 9 · 8 · 0 · 3 (tie rule: equal workout hours → slot with more total effort, then the earlier slot; corrected 1 Oct from 14 · 8, which broke 1 tie by chance) | **Personalised notification timing** |
| **`peak_activity_hour`** **NEW** | Measure | hour with highest average steps | spread 6 AM – 10 PM | Same — finer detail |

*Why steps for the main segment, not active minutes?* Steps are the standard, easy-to-explain measure; `meets_activity_guideline` then corrects for workouts steps can't see. Crosstab: all "Active" and 7 of 10 "Somewhat active" meet the guideline; no "Sedentary" or "Low active" do.

### H4 · Engagement

| Column | Kind | How | Result | Why |
|---|---|---|---|---|
| **`engagement_tier`** **NEW** | Dimension | **Consistent** ≥ 80% clean days · **Irregular** 25–80% · **Barely using** < 25% or `stopped_early` | 20 · 7 · 6 | Main engagement segmentation (fixes the P9 draft cut-offs) |
| `stopped_early`, `stopped_final_week` | Flag | *(decided P10)* | 4 · 8 | Drop-outs |
| `sleep_adoption_level` | Dimension | never · tried · regular · consistent *(decided S8)* | 9 · 8 · 4 · 12 | Sleep-feature adoption |
| `logs_weight`, `logs_workouts`, `n_logged_days` | Flag / Measure | *(decided W7, P6)* | 8 · 3 | Feature adoption |
| `features_used` | Measure | 0–3 *(decided W6)* | 7 · 18 · 7 · 1 | "Feature depth" story |

### H5 · Sleep profile (16 people with ≥ 7 reliable nights)

| Column | Kind | How | Result | Why |
|---|---|---|---|---|
| `typical_sleep_hours`, `typical_sleep_efficiency` | Measure | medians | 12 of 16 typically sleep 7–9 h | Sleep profile |
| `typical_bedtime`, `typical_wake_time` | Measure | medians (bedtime via hours after 6 PM) | wake ≈ 7:02 AM | Timing |
| **`bedtime_group`** **NEW** | Dimension | Early (< 10:30 PM) · Typical · Late (> 12:30 AM) | 4 · 8 · 4 | Evening "wind-down" message timing |
| **`bedtime_regularity`** **NEW** | Measure | variation of bedtime (hours, std) | median ≈ 1 h, range 0.4–3.8 h | Irregular sleep schedule = a sleep-feature hook |
| `nap_rate` **NEW** | Measure | share of days with a nap | — | Napper profile |
| `restless_sleeper` | Flag | efficiency < 85% *(decided S7)* | 1 | Sleep-quality profile |

### H6 · Body & heart (small subsets — always show n)

| Column | Kind | How | Why |
|---|---|---|---|
| `bmi`, `weight_kg`, `bmi_category`, `n_weight_logs`, `manual_share`, `weight_habit` | Measure / Dim / Flag | *(decided W4, W7)* — 8 people | Descriptive BMI mix |
| `typical_resting_hr`, `typical_hr_minutes_above_100` | Measure | medians of daily HR — 12 people *(decided R6, R7)* | Effort detail only |

---

## Decisions needed (all marked NEW)

| # | Decision | Proposal |
|---|---|---|
| F1 | `time_of_day` buckets | Night 0–4 · Morning 5–11 · Afternoon 12–16 · Evening 17–21 · Late 22–23 |
| F2 | Day-level additions | `mvpa_min`, `goal_10k_met`, distance shares, `workout_hour`, `is_worn` |
| F3 | `activity_segment` | Standard step bands on **median** steps (5 · 5 · 10 · 11) |
| F4 | `meets_activity_guideline` | WHO 150 min/week MVPA (18 Yes) |
| F5 | `engagement_tier` | ≥ 80% · 25–80% · < 25% or stopped early (20 · 7 · 6) |
| F6 | Behaviour dimensions | `week_pattern`, `routine_consistency`, `activity_trend`, `preferred_workout_time`, `peak_activity_hour` |
| F7 | Sleep dimensions | `bedtime_group`, `bedtime_regularity`, `nap_rate` |

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | F1–F7 agreed as proposed — moved on to step 1.6 (EDA plan) |
| 2026-10-01 | Phase 2 check — `preferred_workout_time` tie rule added (4 people tied: most effort wins, then the earlier slot) → Morning 13 · Afternoon 9 · Evening 8 · Late 0 · None 3 |
| 2026-10-01 | Phase 2 fix — `preferred_workout_time` label "None" renamed to "No workouts" (pandas reads "None" in CSVs as missing) |