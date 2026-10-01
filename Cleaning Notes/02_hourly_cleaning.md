# 02 · Hourly files (hourlySteps + hourlyCalories + hourlyIntensities) — Cleaning Notes

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning) · **Role:** Time-of-day patterns (when are people active → when to send notifications)

> Running log of problems and solutions. These three files are treated as **one table** because they share exactly the same rows.
> Many hourly problems are **already decided** by the dailyActivity decisions — they are marked "follows P#".

---

## Files at a glance

| Item | Value |
|---|---|
| What it is | One row = one person, one hour. Steps, calories and effort in that hour |
| Size | 22,099 rows in each of the 3 files |
| People | 33 |
| Time range | 12 Apr 2016 00:00 → 12 May 2016 15:00 |
| Blanks / duplicates | None / None |
| Same rows in all 3 files? | ✅ Yes — identical (person, hour) pairs |
| Replaces | All minute-level steps / calories / intensity files (minutes add up exactly to these hours) |
| Clock changes (daylight saving) inside the window? | No (US clocks changed 13 Mar 2016 — before the data starts) |

### Columns we keep / drop

| Keep (renamed) | Drop (and why) |
|---|---|
| Id → `user_id` (text) · ActivityHour → `datetime` · StepTotal → `steps` · Calories → `calories` · TotalIntensity → `intensity` | **AverageIntensity** — exactly TotalIntensity ÷ 60 |

---

## Problem summary

| # | Problem | Solution in one line | Status |
|---|---|---|---|
| H1 | Three separate files for one table | Join on user + hour | ✅ Agreed |
| H2 | Date-time stored as text | Convert with explicit month/day/year hh:mm:ss AM/PM | ✅ Follows P1 |
| H3 | Hours from days we removed in daily | Keep only hours of the 750 valid daily days (757 minus 7 broken) | ✅ Follows P2–P4 |
| H4 | Calories never zero, even with band off | Solved by H3; judge activity by steps/intensity, not calories | ✅ Follows P3 |
| H5 | Hourly steps don't always add up to daily steps; 4 days miss some hours | Accept small gaps; hourly used only for time-of-day patterns, never for totals | ✅ Agreed |
| H6 | Very high hourly values | Keep — nothing impossible | ✅ Follows P8 |
| H7 | Redundant column + messy names | Drop AverageIntensity; snake_case; add hour/day helpers | ✅ Follows P11 |
| H8 | 7 days where every hour = 0 steps but daily shows thousands | Exclude from hourly only | ✅ Follows P4 / P7 |
| H9 | **Effort with zero steps** (e.g., 5 AM workouts) | Keep; flag `stepless_effort` — shows workouts steps can't see | 🟡 Proposed |

**Expected result:** 750 valid days → **17,987 hourly rows**, 33 people.

---

## H1 · Three files for one table — ✅ Agreed

**Evidence** All 3 files have exactly 22,099 rows with the same (person, hour) pairs.

**Solution** Join on `Id` + `ActivityHour` into one `hourly` table.

**How we'll check** Joined table has 22,099 rows before filtering — nothing lost or doubled.

---

## H2 · Date-time stored as text — ✅ Follows P1

`ActivityHour` = "4/12/2016 1:00:00 PM" (American format, AM/PM). Convert with the explicit format. Check: 0 failures; 1:00 PM → hour 13; first = 12 Apr 00:00, last = 12 May 15:00.

---

## H3 · Hours from removed days — ✅ Follows P2–P4

**Evidence** 1,684 hourly rows belong to not-worn days (all 0 steps); plus last days and partial days.

**Solution** Keep only hours whose (user, date) is in `daily_clean` — **except** the 7 broken days (H8). One rule keeps daily and hourly describing the same days.

**Result:** 750 days → 17,987 rows (746 days have all 24 hours).

---

## H4 · Calories never zero — ✅ Follows P3

Minimum hourly calories = 42 even with the band off (the system fills in resting calories). Handled by H3. Rule: judge activity by **steps and intensity**, not calories.

---

## H5 · Hourly ≠ daily, and some hours missing — ✅ Agreed

**Evidence (750 valid days)**
- Hourly steps add up **exactly** to daily steps on **85%** of days. On 95% of days the gap is ≤ 39 steps (≤ 0.44%). Hourly is **never higher** than daily.
- Calories: median gap 0.07%.
- **1 big gap:** 6117666160 on 21 Apr — hourly 9,093 vs daily 19,542 steps. This is the same "half-broken" day from dailyActivity P7 (group B).
- **4 days are missing some hour rows** (the rows simply don't exist):

| Person | Date | Missing hours |
|---|---|---|
| 1503960366 | 11 May | 9 PM – 11 PM |
| 6290855005 | 9 May | 5 PM – 11 PM |
| 8253242879 | 29 Apr | 11 PM |
| 8583815059 | 11 May | 10 PM – 11 PM |

**Why it happens** Small syncing differences; the detailed hourly data is occasionally incomplete while the daily total is complete.

**Solution**
- **Daily totals come from daily_clean. Hourly is used only for time-of-day patterns** (average steps at each hour, weekday × hour heatmap). Never add hourly up to make daily totals.
- Don't fill missing hours (no inventing). For "average steps at hour X", a missing hour simply isn't counted.
- Keep 6117666160 on 21 Apr in hourly (its hours look normal; only the total is higher).

**How we'll check** No chart or number computes daily totals from the hourly table.

---

## H6 · Very high hourly values — ✅ Follows P8

Max 10,554 steps in one hour (user 8877689391, 30 Apr 2 PM, intensity 180 = maximum possible, 948 calories) — a full hour of running by the known runner. Only 1 hour exceeds 10,000. Nothing impossible → keep.

---

## H7 · Columns — ✅ Follows P11

**Drop:** AverageIntensity. **Rename:** snake_case (`user_id`, `datetime`, `steps`, `calories`, `intensity`).

**Add:**

| New column | Why |
|---|---|
| `date` | Link to daily_clean |
| `hour` (0–23) | Time-of-day charts → best notification times |
| `day_of_week`, `is_weekend` | Weekday × hour heatmap |
| `stepless_effort` | H9 |

---

## H8 · Broken hourly days — ✅ Follows P4 / P7

**Evidence** 7 days: all 24 hours = 0 steps while daily shows 3,008–12,015 steps (8583815059 ×5; 4319703577 and 4388161847 on 12 Apr). Their daily effort breakdown is also blank.

**Solution** Excluded from hourly (not in the 750 days). Kept in daily for steps / distance / calories (P7).

---

## H9 · Effort with zero steps — 🟡 Proposed

**What's wrong (simple version)** Some hours show effort (intensity) but **0 steps**. Normally effort comes from walking/running, so how?

**Evidence**
- 183 such hours. 162 are tiny (intensity 1–5 → noise, e.g., arm movement).
- **18 are big** (intensity 96–165, 290–670 calories in one hour) — real workouts with no steps.
- **16 of the 18 = user 8378563200 at 5 AM**, on exactly the days they typed in a workout (dailyActivity P6: 2.09 / 2.25 km). Intensity 165, 669 calories, 0 steps — every time.
- → These are **workouts the step counter can't see** — e.g., cycling, swimming, gym machines — added through the typed-in workout.

- The other 2 big ones (2873212765 at 6 AM, 6290855005 at 9 PM) are on days **without** a typed-in workout → the band itself felt hard effort with no steps.
- Hour-by-hour example (8378563200, 13 Apr): 4 AM → 306 steps, intensity 10 · **5 AM → 0 steps, intensity 165** · 6 AM → 175 steps, intensity 6.
- What kind of workout? About 2 km in an hour of very hard effort fits **swimming or a gym machine** better than cycling (cycling usually covers far more km per hour) — the data can't say for sure.

**Why it matters (Strava angle!)** Step-based measures **under-count** people whose workouts aren't walking/running. This is the closest the data gets to Strava's "cycling / other workouts".
- User 8378563200 ranks **16th of 33 by steps** (middle of the pack) but **4th of 33 by very-active minutes**.
- On their workout days: 78 very-active minutes vs 7.5 on other days.
- → A **steps-only** segmentation would call them "average"; by effort they are among the most active.
- → Segmentation must use **both steps and active minutes** (decision for feature engineering).

**Solution**
- Keep all these hours (real effort).
- Flag `stepless_effort` = Yes when steps = 0 and intensity ≥ 30 (the 18 real ones; ignore the tiny noise).
- In EDA, mention that step counts miss non-walking workouts; use **active minutes / intensity** when comparing workout effort.

**How we'll check** `stepless_effort` = Yes on 18 hours (16 from 8378563200).

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | H2, H3, H4, H6, H7, H8 follow the agreed dailyActivity decisions (P1–P4, P7, P8, P11) |
| 2026-09-30 | H1 agreed — join the 3 hourly files on user + hour |
| 2026-09-30 | H5 agreed — hourly used only for time-of-day patterns, never for daily totals; missing hours not filled |
