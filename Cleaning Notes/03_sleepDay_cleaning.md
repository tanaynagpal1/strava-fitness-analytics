# 03 · sleepDay — Cleaning Notes

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning) · **Role:** Nightly sleep totals · **Status: ✅ ALL 9 PROBLEMS AGREED — plan complete**

> Running log of problems and solutions.

---

## File at a glance

| Item | Value |
|---|---|
| What it is | One row = one person, one sleep date. Minutes asleep, minutes in bed, number of sleeps |
| Size | 413 rows × 5 columns |
| People | 24 (all of them also in dailyActivity) |
| Dates | 12 Apr 2016 → 12 May 2016 |
| Blanks | None |
| Exact duplicate rows | **3** |

### Columns we keep

| Keep (renamed) | Notes |
|---|---|
| Id · SleepDay → `date` · TotalSleepRecords → `sleep_records` · TotalMinutesAsleep → `minutes_asleep` · TotalTimeInBed → `minutes_in_bed` | All 5 columns are useful — nothing to drop |

---

## Problem summary

| # | Problem | Solution in one line | Status |
|---|---|---|---|
| S1 | Exact duplicate rows | Remove duplicates | ✅ Agreed |
| S2 | Date stored as text (with a fake 12:00 AM time) | Convert, keep date only | ✅ Follows P1 |
| S3 | **The date means "the morning you woke up"** | Document it; shift date when linking to that day's activity | ✅ Agreed |
| S4 | Naps are mixed into the night totals | Rebuild night sleep from minuteSleep: main sleep + pieces within 2 h = night; the rest = naps | ✅ Agreed |
| S5 | Very short "nights" (< 3 hours) | Flag `incomplete_night`; daytime-only sessions become naps; exclude from nightly averages AND from `sleep_tracked` | ✅ Agreed |
| S6 | Very long sleeps | 4 sessions stuck at exactly 961 min = recording glitch → flag `capped_session`, exclude like S5; other long nights (10–12 h) are real → keep, flag `long_sleep` | ✅ Agreed |
| S7 | One user is restless in bed a lot | Keep; flag `restless_sleeper` (user level); use medians; no health labels | ✅ Agreed |
| S8 | Users with very few reliable nights | Flag `low_sleep_data_user` (< 7 reliable nights, 8 people); 16 people get sleep profiles; add sleep-feature adoption tier (all 33) | ✅ Agreed |
| S9 | Final sleep table + helper columns | One `sleep_nights.csv` (410 rows) built from minuteSleep + sleepDay; user-level items → user_profile | ✅ Agreed |

---

## S1 · Exact duplicate rows — ✅ Agreed

**Evidence** 3 rows are exact copies:
- 4388161847 on 5 May (471 asleep / 495 in bed)
- 4702921684 on 7 May (520 / 543)
- 8378563200 on 25 Apr (388 / 402)

**Why it matters** Those nights would count twice in averages, and would create doubled rows when joined to dailyActivity.

**Solution** Remove exact duplicates → **410 rows**.

**How we'll check** No (Id, date) appears twice.

---

## S2 · Date stored as text — ✅ Follows P1

**What's wrong** `SleepDay` = "4/12/2016 12:00:00 AM". The time is always 12:00 AM — it carries no information.

**Solution** Convert with month/day/year hour:min:sec AM/PM, then keep only the date. Rename to `date`.

**How we'll check** 0 failures; joins with clean dailyActivity on (Id, date).

---

## S3 · The date means "the morning you woke up" — ✅ Agreed

**What's wrong** It's not obvious which night a date refers to. A sleep from 11 PM on 11 Apr to 7 AM on 12 Apr — is it "11 Apr" or "12 Apr"?

**Evidence** Rebuilding nights from minuteSleep: using the **wake-up date**, time in bed matches sleepDay on **100%** of rows. Using the **start date**, only **37%** match. → `SleepDay` = the date you **woke up**.

**Why it matters** When we join sleep to daily activity on the same date, we get **"last night's sleep → today's activity"**. For the question **"does today's activity affect tonight's sleep?"** we need the *next* date's sleep.

**Solution**
- Keep `date` as the wake-up date (documented).
- When building the daily master table, add two views:
  - `sleep_last_night` = sleep with the same date
  - `sleep_tonight` = sleep with date + 1 day
- Choose the view based on the question being asked.

**Linkage numbers (clean data):** 387 clean daily days have "last night's sleep"; 380 have "tonight's sleep".

**Sleep is cleaned on its own rules.** Removing a daily row (e.g., a partial day) does **not** remove that morning's sleep — the night was recorded fine. 23 of the 410 nights have no matching clean daily day; they stay in **sleep-only** analysis and simply have no activity to compare with.

**Example of how one date works (user 1503960366, 13 Apr):** main sleep 3:08 AM → 8:20 AM **and** a nap 8:10 PM → 9:43 PM. Both carry the date 13 Apr (TotalSleepRecords = 2). → see S4 for separating naps.

---

## S4 · Naps are mixed into the night totals — ✅ Agreed

**What's wrong (simple version)**
sleepDay gives one total per date. If a person slept at night **and** napped in the afternoon, both are added together. So "8 hours of sleep" might really be 5 hours at night + a 3-hour nap.

**Evidence (410 nights)**
- 364 nights = 1 sleep session, **43 = 2 sessions, 3 = 3 sessions** → 49 extra sessions.
- On the 46 multi-session dates, total sleep median = **451 min**, but the main sleep alone = **316 min** → totals inflated by ~2 hours.
- Using minuteSleep, the 49 extra sessions are of **two different kinds**:

| Kind | Count | Example | What it really is |
|---|---|---|---|
| **Piece of a broken night** — starts/ends within **2 h** of the main sleep | **18** | 1503960366: slept 2:11–6:59 AM, then again 7:02–8:19 AM | Woke up briefly and went back to bed → **part of the night** |
| **Real nap** — separate from the night | **31** (9 people) | 3977333714: night 1:04–8:30 AM, nap 3:20–4:34 PM | A **nap** |

- Naps are 60–252 min (median ~2 h), mostly afternoons (1–4 PM) and some evenings (8–10 PM, dozing before bed). 4388161847 naps often (sometimes twice a day).

**Why it matters**
- "Average nightly sleep" would be inflated by naps.
- Treating a broken night's second piece as a "nap" would make restless sleepers look like nappers.
- Bedtime would be wrong if a nap were taken as the start of the night.

**Solution** (built from minuteSleep — see file 04, M5)
1. For each person + wake date: **main sleep** = the longest session.
2. Any other session starting or ending **within 2 hours** of the main sleep → **also night sleep** (broken night).
3. Everything else → **nap**.
4. New columns per night:
   - `night_minutes_asleep`, `night_minutes_in_bed` (main + broken-night pieces)
   - `nap_minutes`, `took_nap` (Yes/No), `night_pieces` (1 = unbroken night)
5. Keep sleepDay's original totals as `total_asleep_incl_naps` / `total_in_bed_incl_naps` for reference.
6. All **nightly** sleep charts use `night_minutes_asleep`.

**How we'll check**
- night + nap minutes = sleepDay totals (time in bed matches 100%, as verified in S3)
- 31 nap sessions from 9 people; 18 broken-night pieces *(corrected 1 Oct: Phase 1 hand count said 30 / 19)*

---

## S5 · Very short "nights" (< 3 hours) — ✅ Agreed

**What's wrong (simple version)**
After S4, 22 dates still have less than 3 hours of night sleep (as low as 58 min). Real adults rarely sleep under 3 hours — more likely **the night wasn't fully recorded**.

**Evidence — two kinds**

| Kind | Count | Examples | What it really is |
|---|---|---|---|
| **A · Only a daytime sleep recorded** (starts 11 AM – 7:49 PM) | **10** | 7007744171 on 1 May: 11:29 AM – 12:29 PM · 1644430081 on 29 Apr: 6:33 – 8:39 PM | A **nap**; the real night was never recorded |
| **B · Night-time start, but cut short** | **12** | 4445114986 on 17 Apr: 2:24 – 4:10 AM · 4558609924: 10:41 PM – 12:41 AM (and 4 more nights like it) · a few 8–10 PM dozes ending before 11 PM | Band removed / battery died mid-night, or an evening doze with the night unrecorded |

- 4558609924 has 5 of the 22 → a recording habit, not a sleep problem.
- **Knock-on effect on dailyActivity P5:** on these days the unrecorded sleep is counted as sitting again — median sitting **1,096 min** vs **712 min** on complete-night days. So these days must NOT count as `sleep_tracked`.

**Night-sleep distribution (all 410 dates)**

| < 3 h | 3–5 h | 5–6 h | 6–7 h | 7–9 h | > 9 h |
|---|---|---|---|---|---|
| 22 | 36 | 52 | 77 | 188 | 35 |

**Solution**
1. Flag `incomplete_night` = Yes when night sleep < 180 min (22 dates).
2. Kind A: move that session to **nap** (night sleep = blank for that date).
3. Exclude all 22 from nightly averages, sleep categories and bedtime/wake-time stats. Keep them in the data (they still count as "sleep feature used").
4. **Update dailyActivity P5:** `sleep_tracked` = Yes only when a **complete** night is recorded → **368** of 757 clean days (was 387); after S6 capped sessions → **365**. `sedentary_awake_min` uses these days only.

**How we'll check**
- 22 dates flagged; 388 complete nights remain for sleep analysis
- Median sitting on `sleep_tracked` days ≈ 712 min

---

## S6 · Very long sleeps — ✅ Agreed

**What's wrong (simple version)**
Some nights show 10–13 hours of sleep. Real (a lie-in after a hard week) or a recording problem?

**Evidence (night sleep after S4, 410 dates)**
- 35 nights > 9 h · **13 nights > 10 h** · 2 nights > 12 h.
- 🚩 **4 sessions last exactly 961 minutes (16 h 01 min)** — same length to the minute, from 2 different people:

| Person | Start | End | Asleep |
|---|---|---|---|
| 1644430081 | 1 May 6:01 PM | 2 May 10:01 AM | 796 |
| 1844505072 | 14 Apr 8:16 PM | 15 Apr 12:16 PM | 644 |
| 1844505072 | 29 Apr 10:09 PM | 30 Apr 2:09 PM | 722 |
| 1844505072 | 30 Apr 8:52 PM | 1 May 12:52 PM | 590 |

Natural sleep never stops at exactly the same minute 4 times → looks like a **recording limit** (the sleep recording kept running until it hit a 16-hour maximum, e.g., sleep mode left on). Lying still in bed gets counted as "asleep", so the minutes are unreliable. 1844505072's typical "night" (644 min) is driven by these.

**The other 10 long nights (10–11.7 h) look real:**

- **6 of 10 are weekend mornings** (Sat/Sun) — lie-ins. (Weekends are only 2 of 7 days.)
- Several follow **very active days**: 5553957443 slept 11 h after 12,764 steps, 10.9 h after 15,482, 10.8 h after 16,556 → recovery sleep.
- One odd case: 5577150313 on 4 May slept **10:30 AM – 9:03 PM** (daytime) — sick day or shift work; keep.

**Solution**
1. Flag `capped_session` = Yes for sessions of exactly 961 min (4 dates) → treat like S5: exclude from sleep-duration averages, categories and bedtime/wake stats; not counted as `sleep_tracked` in daily.
2. Flag `long_sleep` = Yes for other nights > 10 h (10 dates) → **keep** in all analysis (real behaviour).
3. EDA ideas noted: weekend lie-ins; recovery sleep after very active days.

**How we'll check**
- 4 `capped_session` dates, 10 `long_sleep` dates
- No session of exactly 961 min left in duration stats

---

## S7 · One user is restless in bed a lot — ✅ Agreed

**What's wrong (simple version)**
**Sleep efficiency** = time asleep ÷ time in bed. Most people are asleep for ~94% of their time in bed. One person is far below everyone else — error or real?

**Evidence (384 reliable nights — after removing S5 short nights and S6 capped sessions)**
- Median efficiency for everyone: **94%**. Common benchmark for "good" sleep efficiency: **85%+**.
- 28 nights are below 85% and 23 below 70% — and **23 of those 23 belong to one person, 3977333714**.

| Person | Reliable nights | Efficiency (median) | Minutes in bed not asleep (median) |
|---|---|---|---|
| **3977333714** | 27 | **63%** | **162** (155 restless + 4 awake) |
| Next lowest (2347167796) | 15 | 90% | 49 |
| Typical person | — | 94–95% | ~25 |

- It's **consistent**: 23 of their 27 nights are below 70% (range 53–78%). Not one bad night — a pattern.
- It's **spread across the whole night**: 30–43% of every quarter of the night is restless, vs 5–8% for everyone else. So it's not "takes long to fall asleep" — the whole night is broken.
- Mostly marked **restless** (level 2), not fully **awake** (level 3).

**Real or device?** We can't tell for sure — it could be genuinely restless sleep, or the band sensing more movement (e.g., worn loosely). Either way it's consistent, so it's **not a random error**.

**Why it matters**
- Deleting them would hide a real sleep profile — useful for sleep-feature marketing ("improve your sleep quality").
- Keeping them could drag group **averages** down → use **medians** (as agreed in P8).

**Solution**
1. **Keep** all their nights.
2. Flag `restless_sleeper` = Yes at user level (median efficiency < 85% → only 3977333714).
3. Group sleep-quality numbers use **medians**.
4. Use neutral wording only ("restless sleep pattern") — **no health or medical labels**; the data can't diagnose anything.
5. New per-night columns: `sleep_efficiency`, `restless_minutes`, `awake_minutes` (from minuteSleep).

**How we'll check** Group median efficiency ≈ 94% with or without this person; flag = Yes for 1 person.

**Side-finding for S8:** after S5 + S6, only **19 of 24** sleep users have at least one reliable night. 5 people (1644430081, 1844505072, 2320127002, 4558609924, 7007744171) have **only** short or capped nights. *(Corrected from an earlier count of 20/4.)*

---

## S8 · Users with very few reliable nights — ✅ Agreed

**What's wrong (simple version)**
Same idea as dailyActivity P9: you can't describe someone's sleep habits from 2 nights. And after S5/S6, some people have **no** reliable night at all.

**Evidence — reliable nights per person (24 sleep users)**

| Reliable nights | People | Who |
|---|---|---|
| **0** (only short / capped nights) | **5** | 1644430081, 1844505072, 2320127002, 4558609924, 7007744171 |
| 1 – 6 | 3 | 8053475328 (2), 6775888955 (3), 1927972279 (4) |
| 7 – 19 | 4 | 4020332650 (7), 8792009665 (15), 2347167796 (15), 6117666160 (18) |
| **20+** | **12** | the rest |

**Sleep-feature adoption story (all 33 people)** — a ready-made engagement chart:

| Level | People | Share |
|---|---|---|
| Never tracked sleep | 9 | 27% |
| Tried it, but < 7 reliable nights | 8 | 24% |
| Regular (7–19 reliable nights) | 4 | 12% |
| Consistent (20+ reliable nights) | 12 | 36% |

→ Only about **half** of users get real value from sleep tracking. Marketing angle: help the "tried it" group turn it into a habit.

**Solution**
1. Flag `low_sleep_data_user` = Yes for **< 7 reliable nights** (8 people) — same 7-day rule as P9.
2. **Per-person sleep profiles** (typical sleep hours, efficiency, bedtime) → only the **16** people with 7+ reliable nights.
3. **Night-level charts** keep every reliable night from everyone (19 people).
4. Add `sleep_adoption_level` (never / tried / regular / consistent) to user_profile for the engagement page.

**How we'll check** 16 people with sleep profiles; adoption levels add up to 33.

---

## S9 · Final sleep table + helper columns — ✅ Agreed

**Idea (simple version)**
sleepDay and minuteSleep describe the **same nights** at two levels of detail. Instead of two half-useful tables, we build **one clean night table**: the detail (bedtime, naps, restlessness) comes from minuteSleep, the original totals from sleepDay as a cross-check.

### Output: `sleep_nights.csv` — one row per person per wake-up date (410 rows, 24 people)

| Column | Meaning | From |
|---|---|---|
| `user_id` (text), `date` | person, wake-up date | S2, S3 |
| `total_asleep_incl_naps`, `total_in_bed_incl_naps`, `sleep_records` | sleepDay's original numbers (reference only) | S4 |
| `night_minutes_asleep`, `night_minutes_in_bed` | real night sleep (main + broken-night pieces) | S4 |
| `night_hours_asleep` | ÷ 60, easy to read | S9 |
| `sleep_efficiency` | asleep ÷ in bed | S7 |
| `minutes_awake_in_bed`, `restless_minutes`, `awake_minutes` | quality detail | S7 |
| `night_pieces` | 1 = slept straight through | S4 |
| `bedtime`, `wake_time` (clock time) | start of first / end of last night piece | S4 |
| `bedtime_hrs_after_6pm` | e.g., 11:30 PM → 5.5, 12:30 AM → 6.5 (so averages work across midnight) | M6 |
| `nap_minutes`, `took_nap` | naps that day | S4, S5 |
| `incomplete_night`, `capped_session`, `long_sleep` | flags | S5, S6 |
| `reliable_night` | Yes if not incomplete and not capped (**384** nights) | S5, S6 |
| `sleep_category` | < 6 h · 6–7 h · **7–9 h (recommended)** · > 9 h — reliable nights only | S9 |
| `day_of_week`, `is_weekend_morning` | weekend lie-in analysis | S6 |

**Goes to user_profile (not this table):** `low_sleep_data_user`, `restless_sleeper`, `sleep_adoption_level`, typical sleep hours / efficiency / bedtime (medians, 16 people).

**Goes to daily master (when joining):** `sleep_last_night` / `sleep_tonight` (S3), `sleep_tracked` = reliable night on that date (365 clean days).

**How we'll check**
- 410 rows, 24 people, no duplicate (user_id, date)
- night + nap minutes = sleepDay totals (time in bed 100% match)
- 384 reliable nights; `sleep_category` blank on the other 26
- Median night sleep ≈ 7 h 13 min (433 min); median efficiency ≈ 94%; median bedtime ≈ 11:13 PM
- Sleep categories (reliable nights): < 6 h: 86 · 6–7 h: 78 · 7–9 h: 189 · > 9 h: 31

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | S1 agreed — remove 3 exact duplicates (413 → 410) |
| 2026-09-30 | S2 follows P1 — explicit format, keep date only |
| 2026-09-30 | S3 agreed — `date` = wake-up date; daily master gets `sleep_last_night` (same date) and `sleep_tonight` (next date); sleep cleaned independently of daily removals |
| 2026-09-30 | S4 agreed — night = main session + pieces within 2 h; others = naps; new `night_minutes_asleep`, `nap_minutes`, `took_nap`, `night_pieces`; sleepDay totals kept as *incl_naps* |
| 2026-09-30 | S5 agreed — `incomplete_night` (< 180 min, 22 dates); daytime-only sessions → naps; excluded from nightly stats; `sleep_tracked` in daily only for complete nights (368 days) |
| 2026-09-30 | S6 agreed — 4 sessions of exactly 961 min flagged `capped_session` and excluded from duration stats (like S5); other > 10 h nights kept as `long_sleep`; `sleep_tracked` in daily → 365 days |
| 2026-09-30 | S7 agreed — keep 3977333714's nights; user flag `restless_sleeper` (median efficiency < 85%); medians for group sleep quality; neutral wording, no health labels |
| 2026-09-30 | S8 agreed — `low_sleep_data_user` (< 7 reliable nights, 8 people); sleep profiles for 16 people; night charts use all reliable nights (19 people); `sleep_adoption_level` for all 33 |
| 2026-09-30 | S9 agreed — one `sleep_nights.csv` (410 rows, 24 people) built from minuteSleep detail + sleepDay totals; bedtime as hours after 6 PM; user-level sleep items → user_profile |
| 2026-10-01 | Phase 2 check — S4 recount: **31 naps · 18 night pieces** (not 30 / 19). Rule unchanged; the borderline session (4445114986, 6 May: back in bed 2 h 01 min after waking) is a nap. Night totals, 410 nights and 384 reliable nights unchanged |
