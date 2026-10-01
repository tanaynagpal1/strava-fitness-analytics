# 05 · weightLogInfo — Cleaning Notes

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning) · **Role:** BMI profile + feature adoption · **Status: ✅ ALL 7 PROBLEMS AGREED — plan complete**

> Running log of problems and solutions.

---

## File at a glance

| Item | Value |
|---|---|
| What it is | One row = one weight entry: weight, BMI, body fat, typed by hand or smart scale |
| Size | 67 rows × 8 columns |
| People | **8 of 33** (24%) |
| Dates | 12 Apr 2016 → 12 May 2016 |
| Duplicate rows / same person twice on one day | None / None |
| Blanks | **Fat: 65 of 67 empty** |

### Columns we keep / drop

| Keep (renamed) | Drop (and why) |
|---|---|
| Id · Date → `date` · WeightKg → `weight_kg` · BMI → `bmi` · IsManualReport → `is_manual` | **Fat** — 97% empty · **WeightPounds** — just kg × 2.2046 · **LogId** — a record number, not unique across people |

---

## Problem summary

| # | Problem | Solution in one line | Status |
|---|---|---|---|
| W1 | Fat column almost empty | Drop it | ✅ Agreed |
| W2 | Duplicate information / ID columns | Drop WeightPounds and LogId | ✅ Agreed |
| W3 | Date-time stored as text | Convert; keep date only | ✅ Follows P1 |
| W4 | Very uneven entries per person | Summarise to one row per person (median) | ✅ Agreed |
| W5 | One very high BMI (47.5) | Keep — consistent and possible; use median + categories | ✅ Agreed |
| W6 | Only 8 people | Use as descriptive profile + feature-adoption signal only; no BMI-vs-activity claims | ✅ Agreed |
| W7 | Final tables + helper columns | `weight_logs_clean.csv` (67) + `user_body_profile` (8); WHO BMI categories; `logs_weight`, `features_used` for all 33 | ✅ Agreed |

---

## W1 · Fat column almost empty — ✅ Agreed

**Evidence** Only 2 of 67 entries have a Fat value: 1503960366 on 2 May (22%) and 4319703577 on 17 Apr (25%) — both typed by hand, once each.

**Solution** Drop. Two values can't support any analysis, and filling 65 blanks would be inventing data.

---

## W2 · Duplicate information / ID columns — ✅ Agreed

**Evidence**
- WeightPounds = WeightKg × 2.20462 on every row.
- LogId is **not unique**: it is simply the entry's **date-time written as milliseconds since 1970** (e.g., 1462233599000 = 2 May 2016 11:59:59 PM). Manual entries are all stamped 11:59:59 PM, so two people typing on the same date get the same LogId — 10 LogIds are shared between people. It adds nothing the Date column doesn't already have.

**Solution** Drop both. We use kg (standard for India/most of the world).

---

## W3 · Date-time stored as text — ✅ Follows P1

**Evidence** All 41 manual entries are stamped "11:59:59 PM" (the person entered only a date). Smart-scale entries carry the real time — mostly **6:39–6:51 AM** → a morning weigh-in routine.

**Solution** Convert with month/day/year hour:min:sec AM/PM, keep date only → `date`.

---

## W4 · Very uneven entries per person — ✅ Agreed

**Evidence**

| Person | Entries | Avg BMI | Avg kg | Entry type |
|---|---|---|---|---|
| 6962181067 | 30 | 24.0 | 61.6 | Manual |
| 8877689391 | 24 | 25.5 | 85.1 | Smart scale |
| 4558609924 | 5 | 27.2 | 69.6 | Manual |
| 1503960366 | 2 | 22.6 | 52.6 | Manual |
| 2873212765 | 2 | 21.6 | 57.0 | Manual |
| 4319703577 | 2 | 27.4 | 72.4 | Manual |
| 1927972279 | 1 | 47.5 | 133.5 | Smart scale |
| 5577150313 | 1 | 28.0 | 90.7 | Smart scale |

Two people = 54 of 67 rows (81%). Weight barely changes in a month (max change 1.8 kg).

**Why it matters** Averaging all rows would mostly describe 2 people.

**Solution**
1. Keep the cleaned entry-level table (`weight_logs_clean.csv`, 67 rows) for a simple "weight over time" view of the 2 regular loggers.
2. Summarise to **one row per person** (`user_body_profile`, 8 rows):
   - `bmi` and `weight_kg` = **median** of their entries (same rule as P8; weight changes ≤ 1.8 kg in the month, so median ≈ latest)
   - `n_weight_logs`, `manual_share`, `first_log_date`, `last_log_date`
3. Every person counts **once** in BMI charts — no matter whether they logged 1 time or 30.

**How we'll check** `user_body_profile` has 8 rows; the two heavy loggers count once each.

---

## W5 · One very high BMI — ✅ Agreed

**Evidence** User 1927972279: 133.5 kg, BMI 47.5. Check: implied height = √(kg ÷ BMI) = **1.68 m**, a normal height. Implied height is constant for every person across all their entries → BMI values are internally consistent.

**More checks**
- Recorded **automatically by a smart scale** (IsManualReport = False) → not a typing mistake.
- Implied heights for all 8 people range 1.52 – 1.83 m and stay **constant** across every person's entries → BMI is calculated consistently.
- It fits the rest of this person's data: lowest typical steps of anyone (≈ 2,163 on clean days), 13 not-worn days, 7 clean days.

**Effect on group numbers (8 people)**
- **Mean** BMI = 28.0 — pulled up by this one person
- **Median** BMI = 26.4 — not affected

**Solution**
1. **Keep.** Possible, consistent, machine-recorded — not an error.
2. Group BMI = **median** + **category counts** (W7), never the plain mean.
3. Neutral wording only (use the standard category names; no personal remarks).

---

## W6 · Only 8 people — ✅ Agreed

**What's wrong (simple version)**
Only 8 of 33 people ever logged their weight. With 8 people, any "BMI affects activity" conclusion would be a guess — one person changes the whole picture.

**What we CAN and CAN'T say**

| ✅ Can say (descriptive / engagement) | ❌ Can't say (too few people) |
|---|---|
| BMI mix of those who log: 3 normal, 4 overweight, 1 obese (median BMI 26.4) | "Higher BMI → fewer steps" or any BMI-vs-activity relationship |
| Only **24%** of users ever logged weight | "Overweight users sleep less" etc. |
| Only **2 of 8** built a habit (30 and 24 entries); 6 logged 1–5 times and stopped | Anything about BMI for the other 25 users |
| 5 of 8 typed by hand, 3 used a smart scale; scale users weigh in at ~6:45 AM | |
| Weight loggers look slightly more engaged: typical 8,863 steps vs 8,053; 28.5 clean days vs 26 (directional only) | |

**Bigger engagement idea found while checking — "feature depth"**
Counting how many *optional* features each person uses (sleep tracking, weight logging, workout logging):

| Optional features used | People | Typical steps | Typical clean days |
|---|---|---|---|
| 0 | 7 | 7,396 | 24 |
| 1 | 18 | 8,409 | 28 |
| 2 | 7 | 8,596 | 27 |
| 3 | 1 | 10,479 | 30 |

→ People who use **more features** tend to be **more active and wear the band more**. Small numbers and not cause-and-effect (active people may simply like more features), but a strong marketing story: *get users to adopt a second feature*.

**Solution**
1. Use weight/BMI only for: (a) the descriptive BMI mix, (b) feature-adoption numbers. Every chart states **"n = 8 users"**.
2. **No** BMI-vs-activity or BMI-vs-sleep claims.
3. Add `features_used` (0–3) to user_profile for the engagement page.

---

## W7 · Final tables + helper columns — ✅ Agreed

### Output 1 · `weight_logs_clean.csv` — one row per entry (67 rows, 8 people)

| Column | Notes |
|---|---|
| `user_id` (text), `date` | W3 |
| `weight_kg` | 1 decimal (raw has noise like 52.599998) |
| `bmi` | 1 decimal |
| `is_manual` | Yes = typed by hand, No = smart scale |
| `bmi_category` | see below |

### Output 2 · `user_body_profile` — one row per person (8 rows)

| Column | How |
|---|---|
| `bmi`, `weight_kg` | **median** of their entries (W4) |
| `bmi_category` | from median BMI |
| `n_weight_logs` | count of entries |
| `manual_share` | share typed by hand |
| `first_log_date`, `last_log_date` | first / last entry |
| `weight_habit` | Yes if ≥ 10 entries (the 2 regular loggers) |

### BMI categories (WHO international standard)

| BMI | Category | People |
|---|---|---|
| < 18.5 | Underweight | 0 |
| 18.5 – 24.9 | Normal | 3 |
| 25 – 29.9 | Overweight | 4 |
| ≥ 30 | Obese | 1 |

*Note:* India/Asia often uses lower cut-offs (23 / 27.5). The data doesn't say where users live, so we use the WHO international standard and state it on the chart.

### Goes to user_profile (all 33 people)
- `logs_weight` (Yes/No) — 8 Yes / 25 No
- `features_used` (0–3) = sleep tracking + weight logging + workout logging (W6)
- plus the 8 rows of `user_body_profile` joined in (blank for the other 25)

**How we'll check**
- 67 entry rows, 8 profile rows, no Fat / WeightPounds / LogId columns
- Category counts 0 / 3 / 4 / 1; `features_used` counts 7 / 18 / 7 / 1

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | W1, W2 agreed — drop Fat (97% empty), WeightPounds (duplicate), LogId (date-time in ms, not unique) |
| 2026-09-30 | W3 follows P1 — explicit format, keep date only |
| 2026-09-30 | W4 agreed — one row per person (`user_body_profile`, 8 rows) using median BMI/weight; entry list kept for over-time view |
| 2026-09-30 | W5 agreed — keep BMI 47.5 (smart scale, consistent height); group BMI = median (26.4) + category counts; neutral wording |
| 2026-09-30 | W6 agreed — weight/BMI used only for descriptive BMI mix + feature adoption (n = 8 on every chart); no BMI-vs-activity claims; add `features_used` |
| 2026-09-30 | W7 agreed — outputs `weight_logs_clean.csv` (67) + `user_body_profile` (8, median BMI, WHO categories stated on chart); `logs_weight` + `features_used` for all 33 |
