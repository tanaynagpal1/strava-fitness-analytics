# 01 · dailyActivity — Cleaning Notes

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning) · **Role:** MAIN file · **Status: ✅ ALL 11 PROBLEMS AGREED — plan complete**

> This is a running log. Each problem we find is written down with its evidence, why it matters, the solution, and how we will check the fix worked. Status shows whether we have agreed on it.

---

## File at a glance

| Item | Value |
|---|---|
| What it is | One row = one person, one day. Steps, distance, minutes at each effort level, calories |
| Size | 940 rows × 15 columns |
| People | 33 |
| Dates | 12 Apr 2016 → 12 May 2016 (31 days) |
| Blanks / duplicate rows / negative values | None / None / None |
| Replaces | dailyCalories, dailySteps, dailyIntensities (100% identical data — not used) |

### Columns we keep / drop

| Keep | Drop (and why) |
|---|---|
| Id, ActivityDate → `date`, TotalSteps, TotalDistance, VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes, SedentaryMinutes, Calories, LoggedActivitiesDistance, VeryActiveDistance, ModeratelyActiveDistance, LightActiveDistance | **TrackerDistance** — same as TotalDistance except on hand-logged workout days · **SedentaryActiveDistance** — almost always 0 (max 0.11 km) |

---

## Problem summary

| # | Problem | Solution in one line | Rows affected | Status |
|---|---|---|---|---|
| P1 | Date stored as text | Convert to real date using month/day/year | all | ✅ Agreed |
| P2 | Incomplete last days | Remove each person's final recorded day | −33 | ✅ Agreed |
| P3 | Band not worn (zero / near-zero step days) | Count them per user, then remove days with < 100 steps | −77 | ✅ Agreed |
| P4 | Band worn only part of the day | Remove days with movement in fewer than 10 different hours | −73 | ✅ Agreed |
| P5 | Sitting time recorded two ways | Flag `sleep_tracked`; create `sedentary_awake_minutes` (sleep-tracked days only); active minutes = main measure | 0 (new columns) | ✅ Agreed |
| P6 | TotalDistance ≠ TrackerDistance | Use TotalDistance; drop TrackerDistance; turn logged distance into a workout-logging flag | 0 | ✅ Agreed |
| P7 | Effort-level breakdown missing on some days | Blank the breakdown on 7 days (flag `breakdown_missing`); keep their steps/distance/calories | 0 (7 days blanked) | ✅ Agreed |
| P8 | Very high / very low values (possible outliers) | Keep all (none impossible); use **median** for each person's typical day | 0 | ✅ Agreed |
| P9 | Some users have very few clean days | Flag users with < 7 clean days: out of activity profiles/segments, **in** engagement analysis | 0 (flag) | ✅ Agreed |
| P10 | Missing calendar days (people who stopped) | Never fill; mark `stopped` in wear_log; drop-out flags; trend charts show users-per-week | 0 | ✅ Agreed |
| P11 | Messy / unneeded columns | Drop 2, rename all to simple names, fix types, add helper columns; fixed cleaning order | 0 | ✅ Agreed |

**Expected result:** 940 → **757 rows**, still **33 people**.

---

## P1 · Date stored as text — ✅ Agreed

**What's wrong**
`ActivityDate` looks like a date ("4/12/2016") but Python reads it as plain text, like a word.

**Evidence**
- Text sorting puts `5/10/2016` before `5/2/2016` (it compares letter by letter).
- Joining dailyActivity with sleepDay on the text dates matched **0 rows**, because sleepDay writes the same day as `4/12/2016 12:00:00 AM`. After converting both to real dates: **410 matches**.
- The dates are American format (**month/day/year**). Reading them the Indian way (day/month/year) turns 4/12/2016 into **4 December** and fails on **578 of 940 rows** ("month 13" doesn't exist).

**Why it matters**
Wrong order in trend charts, no weekday/weekend analysis, and a silent failure when joining with sleep data.

**Solution**
1. Convert `ActivityDate` to a real date, stating the format explicitly: month/day/year.
2. Rename it to `date` (same name in every file → easy joins).

**How we'll check**
- 0 conversion failures
- Earliest date = 12 Apr 2016, latest = 12 May 2016
- 12 Apr 2016 shows as **Tuesday**
- Join with sleepDay returns 410 matches

---

## P2 · Incomplete last days — ✅ Agreed

**What's wrong**
The data was exported partway through **12 May 2016** (nothing recorded after ~3 PM). Also, **12 people stopped wearing the band before 12 May**, and their own last day is incomplete too (the day they took it off).

**Evidence**

| Middle value | Normal day | 12 May |
|---|---|---|
| Steps | 8,148 | 3,121 |
| Calories | 2,227 | 1,212 |
| Active minutes | 258 | 71 |
| Minutes recorded | 1,364 | 910 |

Examples of early-stoppers' last days: user 4057192912 on 15 Apr (970 min recorded), 3372868164 on 1 May (1,014 min), 6775888955 on 7 May (607 min), 1644430081 on 11 May (762 min). On their other days these users record the full 1,440 minutes.

**Why it matters**
Keeping them creates a false "drop" at the end of the month in trend charts → a wrong story that "users lost interest". It also lowers everyone's averages.

**Solution**
Remove **each person's final recorded day** (12 May for 21 people; the stop day for the other 12). Never scale a partial day up — that would be inventing data.

**How we'll check**
- No 12 May rows remain
- Each person has exactly one fewer day
- Still 33 people
- Month trend line no longer dips at the end

**Rows removed:** 33 (940 → 907)

---

## P3 · Band not worn (zero / near-zero step days) — ✅ Agreed (option B)

**What's wrong**
Some days show 0 steps and "sitting for 1,440 minutes" — a whole day without a single movement. That is not a lazy person; it is a day with **no wear data**. A few more days show a tiny number of steps (4, 8, 16, 44…) all inside **one single hour**, and nothing else all day — the band was briefly handled, not worn.

**Evidence (after P2)**
- **69 days with 0 steps** — 68 of them are exactly 1,440 sitting minutes; together they contain only 33 active minutes in total.
- **8 more days with 1–100 steps**, all with 1,366–1,440 minutes "recorded" (e.g., user 1844505072: 8, 4 and 44 steps on three different days).
- Even a sick person at home walks a few hundred steps a day (bathroom, kitchen) — under 100 steps in 24 hours is not a real day of wear.
- **Calories trap:** these days still show ~1,841 calories (median). The device fills in an estimate of resting calories whether or not it's worn — so calories alone can't tell us the band was worn.
- **It's concentrated:** 12 users have zero-step days. User 4020332650 didn't wear the band on **47%** of their days, 1927972279 on **43%**, 6775888955 on **36%**.

**Why it matters**
- Average steps per day: **7,814 with these days vs 8,457 without** — keeping them understates activity by ~8%.
- 2 users land in the wrong segment: 4057192912 (Sedentary → actually Low), 6117666160 (Low → actually Somewhat active).
- For a marketing project, wrongly calling people "sedentary" means sending them the wrong message.

**Solution**
1. **Before deleting**, count each user's non-wear days → `non_wear_days` (goes into the user profile as an **engagement signal** — "how often does this person leave the band at home?").
2. Remove days where `TotalSteps < 100` (covers the 69 zero days + 8 near-zero days).

| Option | Rows removed | Recommendation |
|---|---|---|
| A · Remove only `TotalSteps = 0` | 69 | OK, but leaves 8 obvious non-wear days |
| **B · Remove `TotalSteps < 100`** | **77** | ✅ **Recommended** |

**How we'll check**
- Minimum TotalSteps in clean file ≥ 100
- No rows with 0 calories
- `non_wear_days` column exists for all 33 users (0 for 21 users)

**Rows removed:** 77 with option B (907 → 830).

### P3 add-on · Keep non-wear for the dashboard (Tanay's idea) — ✅ Agreed

Before removing rows, save a separate small table **`wear_log`** — one row per person per calendar day (33 × 31) with a status:
`worn` · `not_worn` (< 100 steps) · `partial` (movement in < 10 hours, see P4) · `last_day` · `stopped` (no row — after the person quit).
The analysis tables stay clean; the dashboard's Engagement page uses `wear_log`.

**What the data says about WHY people leave the band off** (patterns, not proven reasons — there's no survey data):

| Possible reason | Evidence | Verdict |
|---|---|---|
| Holidays | No user location in data; no major public holidays in 12 Apr–12 May 2016 | ❌ Can't test / unlikely |
| Weekends | Weekend 9.5% vs weekday 8.1%; Sunday highest (10.8%) but only 7–13 days per weekday | ❌ No clear pattern |
| **Took it off and forgot (e.g., charging)** | 22 of 35 breaks are a **single day**. Day before a break: last step at **5 PM** (median) vs 11 PM normally; **33%** of those days end by 2 PM vs 2% normally. Day after is also short (3,421 steps) → put back on mid-day | ✅ **Strongest pattern** |
| **Novelty wearing off** | Non-wear rate week 1: 6.6% → weeks 2–4: 9–10%. 12 users stopped completely before 12 May (all 83 missing calendar days come after they quit) | ✅ Supported |
| **Less active people wear it less** | On worn days: 6,757 steps (users with non-wear days) vs 9,031 (always-wear); correlation −0.58 | ✅ Supported |
| Long breaks (travel / illness / gave up) | A few multi-day breaks, one of 15 days | ⚠️ Can't tell which |

**Tanay's battery hypothesis — tested** ("0 steps = forgot to charge; 1–100 steps = low battery that ran out"):

| Test | Result | What it means |
|---|---|---|
| Are zero days really "recorded"? | Each user's zero days show the **exact same calories** every time (e.g., 1844505072: always 1,347; 6775888955: always 1,841); no heart rate on 38 of 40; effort = resting all day | The system **fills an empty day** with a fixed resting-calorie estimate and "sitting" minutes. So zero days = **no data** — dead battery, left at home or left on the charger all look identical. ⚠️ Can't prove "forgot to charge" |
| When do the steps happen on 1–100 step days? | All in **one single hour**, 6 of 8 between 7 PM and midnight (e.g., 8 steps at 10 PM) | A battery dying *during use* would show steps from the morning until it died. A single late burst looks like the band being **picked up / moved / put on a charger**. ❌ Doesn't fit "ran out during use" |
| Where DOES the battery idea fit? | Day **before** a break: recording stops early (median 5 PM; 33% by 2 PM vs 2% normally) | Consistent with the battery **dying during the day** (or being taken off to charge) and not being recharged → next day empty. ✅ Plausible |

**Decision for labels:** dashboard says "Not worn" (with sub-types *no data* / *briefly handled*), and describes charging as the **likely** cause, not a proven one.

**Marketing use:** "band off for X hours — put it back on" reminders; battery/charging reminders; re-engagement push around week 2; low-activity users are the priority group for engagement campaigns.

---

## P4 · Band worn only part of the day — ✅ Agreed (10 movement hours)

**What's wrong**
Some days have real steps, but the band was only on for part of the day (e.g., put on at 8 AM, taken off at 1 PM). The rest of the day looks like "no activity", so the day looks much lazier than it was.

**Why the original rule (`wear_minutes` < 600) doesn't work** — found while checking:
1. **The system fills missing time with "sitting".** On days without a sleep record, **92%** add up to exactly 1,440 minutes — even when the band was clearly off for most of the day. Example: user 8792009665 on 21 Apr: 144 steps, all at midnight, yet "1,440 minutes recorded". So `wear_minutes` can't see partial wear.
2. **It catches the wrong days.** Only 2 days fall below 600 minutes, and both are **long-sleep days**, not partial wear: 1844505072 on 30 Apr (402 min + 961 min in bed) and 5553957443 on 30 Apr (590 min + 843 min in bed). Removing them would delete real days.

**Better measure: `movement_hours`**
Count how many of the 24 hours contain **at least 1 step** (from the hourly file). An awake person gets up at least once in almost every hour; a band lying somewhere records none.

**Evidence**

| Hours with movement | Days | Median steps |
|---|---|---|
| 1–6 | 40 | 1,521 |
| 6–8 | 23 | 3,414 |
| 8–10 | 25 | 3,790 |
| 10–12 | 69 | 6,017 |
| 12–24 | 666 | 9,146 |

Median day = 16 movement hours. 28 days have movement that **stops by 2 PM** (e.g., 1927972279 on 7 May: moves only 10–11 AM) and 15 days where movement **starts after 2 PM** — yet 23 of those early-stop days still claim "1,440 minutes recorded". The short days are concentrated in the same people who leave the band off (6775888955: 12 days, 1927972279: 10) → a **wear problem**, not laziness.

**Threshold options (after P2 + P3)**

| Rule: keep days with movement in ≥ … hours | Rows removed | Users changing activity segment |
|---|---|---|
| 6 | 31 | 3 |
| 8 | 50 | 4 |
| **10** | **73** | 6 |
| 12 | 114 | 8 |

**Solution**
- Create `movement_hours` from the hourly file.
- Remove days with **movement_hours < 10** — our version of the common "10 hours of wear" rule.
- **Exception — 7 days where the hourly file is broken:** daily shows real steps (3,008 – 12,015) but all 24 hourly rows show 0 (users 8583815059 ×5, 4319703577 and 4388161847 on 12 Apr). Trust the daily totals → **keep these days**, and exclude them from hourly analysis (see hourly file, H8). Their effort-level breakdown is also missing → handled in P7.
- Mark removed days as `partial` in `wear_log` (P3 add-on) before removing them.
- Drop the idea of `wear_minutes` as a filter.

**How we'll check**
- Every remaining day has `movement_hours ≥ 10` (or is one of the 7 broken-hourly days)
- Still 33 users
- The long-sleep days of 30 Apr are still present

**Rows removed:** 73 (830 → 757)

---

## P5 · Sitting time recorded two ways — ✅ Agreed (option B)

**What's wrong (simple version)**
Think of each day as a 1,440-minute pie.
- **Nights when sleep was recorded:** pie = active + sitting + **sleep** → sleep is its own slice.
- **Nights when sleep was NOT recorded:** pie = active + sitting → **sleep gets counted as sitting** (the same "fill empty time as sitting" behaviour found in P3/P4).

**Evidence (on the 757 clean days)**

| | Sleep recorded (387 days) | Sleep not recorded (370 days) |
|---|---|---|
| Median sitting time | **717 min (12.0 h)** | **1,157 min (19.3 h)** |
| Median active minutes | 267 | 274 |
| Days adding up to exactly 1,440 min | 0% | 93% |

- On sleep days: active + sitting + time in bed = **exactly 1,440** (median) → the pie theory is confirmed.
- **Same-person proof:** 12 users have both kinds of days. For the *same person*, sitting jumps by **~388 min (6.5 h)** on nights without a sleep record, while active minutes barely change (~11 min). A person doesn't suddenly sit 6.5 hours more — the "extra sitting" is their **sleep**.

**Second trap — the "sitting vs sleep" relationship is forced by maths**
Even on sleep days, sitting and sleep have a −0.69 correlation. That's not a behaviour insight: the pie is fixed at 1,440, so more sleep *must* leave less room for sitting. **We will not present sitting-vs-sleep correlation as a finding.**

**Why it matters**
Raw averages would say people sit 16–20 hours a day, and anyone who didn't track sleep would look like a couch potato.

**Options**

| Option | What | Verdict |
|---|---|---|
| A · Flag only | Add `sleep_tracked`, analysts must remember to filter | OK, but easy to misuse |
| **B · Flag + safe column** | Add `sleep_tracked` and a new column `sedentary_awake_minutes` = SedentaryMinutes on sleep-tracked days, **blank** on others. Keep raw column but never chart it | ✅ **Recommended** |
| C · Guess sleep and subtract it (e.g., −7 h) | Would fill 370 days with invented numbers | ❌ Inventing data |

**Solution (option B)**
1. Add `sleep_tracked` (Yes/No) from clean sleepDay.
2. Add `sedentary_awake_minutes` — filled only on sleep-tracked days.
3. **Active minutes** (Very + Fairly + Lightly) and **steps** are our main activity measures — they're unaffected (same-person difference ~11 min).
4. Every sitting-time chart uses `sedentary_awake_minutes` and shows a note: "based on 365 days with a complete night of sleep recorded".
5. Even this column may hide some band-off daytime (filled as sitting) — treat sitting time as the **least reliable** measure.

**Coverage after the fix:** sitting-time analysis possible for 24 users (16 with 7+ days); 9 users never tracked sleep → no sitting number for them.

**How we'll check**
- `sleep_tracked` = Yes on **365** of 757 days (updated by sleepDay S5/S6: only **complete, reliable** nights count — 19 short-night days and 3 capped-session days excluded)
- `sedentary_awake_minutes` blank on the other 392
- Median `sedentary_awake_minutes` ≈ 712 (12 h)

---

## P6 · TotalDistance ≠ TrackerDistance — ✅ Agreed

**What's wrong (simple version)**
There are three distance columns:
- **TrackerDistance** — what the band measured by itself
- **LoggedActivitiesDistance** — a workout the person **typed into the app** (e.g., "I ran 5 km")
- **TotalDistance** — the final number the app shows = band distance + any part of the typed workout the band **didn't already catch**

They usually match, but differ on 15 days. Which one should we use?

**Evidence (757 clean days)**
- Only **31 days** have a typed-in workout, from only **3 of 33 users** (9%).
- TotalDistance is **never smaller** than TrackerDistance.
- The difference is **smaller than** the typed distance: e.g., 6962181067 on 9 May typed 3.17 km but TotalDistance is only 0.04 km above TrackerDistance → the band had already recorded most of that workout; the app only added what was missing (no double counting).
- User 8378563200 typed a workout on 16 days (always 2.09 or 2.25 km) and the gap is **0** every time → the band had already caught the whole workout.
- Typed-in distance = only **2%** of all kilometres → tiny effect on distance analysis.

**Engagement finding**
The 3 people who type workouts do it as a **routine**: 7007744171 on 12 days (~4.9 km almost every time), 8378563200 on 16 days (2.09 / 2.25 km), 6962181067 on 3 days. Few users use the feature, but those who do use it regularly — a **feature-adoption opportunity** for marketing.

**Solution**
1. Use **TotalDistance** as the one distance measure (it's the complete, already de-duplicated number).
2. **Drop TrackerDistance.**
3. **Don't** add LoggedActivitiesDistance to TotalDistance — that would double count.
4. Turn LoggedActivitiesDistance into:
   - `logged_workout` (day level, Yes/No)
   - `logs_workouts` + `n_logged_days` (user level, for the engagement page)

**Unit note:** ~1,465 steps per unit of distance = a normal walking stride in **kilometres**. Label all distances in km.

**How we'll check**
- TrackerDistance no longer in the table
- `logged_workout` = Yes on 31 days, 3 users

---

## P7 · Effort-level breakdown missing on some days — ✅ Agreed (blank the breakdown)

**What's wrong (simple version)**
Each day has totals (steps, TotalDistance, calories) **and** a breakdown by effort level (very / fairly / light active minutes and distances). The breakdown should add up to the total. On some days it doesn't.

⚠️ **Correction:** earlier notes said the cause was hand-logged workouts. Checking the 757 clean days proved that wrong — on logged-workout days the breakdown adds up fine. The real causes are below.

**Evidence (17 days where breakdown ≠ total by more than 0.1 km)**

| Group | Days | What we see | Meaning |
|---|---|---|---|
| **A · Breakdown completely missing** | **7** | Real steps (3,008 – 12,015) and distance, but **0 active minutes, 1,440 sitting minutes, 0 km in every effort level**. Same 7 days as the broken hourly days (P4 / H8): 8583815059 ×5, 4319703577 and 4388161847 on 12 Apr | The detailed minute data never arrived; only the daily totals survived. "0 active minutes with 12,015 steps" is **wrong** |
| B · Breakdown half missing | 1 | 6117666160 on 21 Apr: 19,542 steps, 15.0 km, but effort levels add to only 7.0 km | Part of the day's detail missing; totals look real |
| C · Small gaps | 9 | 0.1 – 0.8 km differences | Rounding / small sync differences — ignore |

**Why it matters**
Group A would add 7 days of "**0 active minutes**" — our **main activity measure** (P5) — to users who actually walked thousands of steps. It would also put 1,440 fake sitting minutes into sitting-time analysis.

**Options for group A**

| Option | What | Verdict |
|---|---|---|
| Remove the 7 days | Simple, but deletes real steps/distance/calories | OK |
| **Blank the breakdown** | Keep steps, distance, calories. Set the 4 minute columns and 4 effort-distance columns to **blank** on these 7 days, add flag `breakdown_missing` = Yes. Averages automatically skip blanks | ✅ **Recommended** — keeps real data, removes wrong data |
| Leave as is | 0 active minutes stays in | ❌ Wrong numbers |

**Solution**
1. Group A (7 days): blank the breakdown columns, set `breakdown_missing` = Yes.
2. Group B (1 day): keep as is; use effort-level distances only as **shares**, never as totals.
3. Group C: no action.
4. Drop SedentaryActiveDistance (only 1.46 km in the whole month — see P11).

**Useful fact for EDA:** share of distance by effort level — **Light 61%**, **Very active 28%**, **Moderate 10.5%**.

**How we'll check**
- 7 days have `breakdown_missing` = Yes and blank minute columns
- No remaining day has steps > 1,000 with 0 active minutes AND 1,440 sitting minutes

---

## P8 · Very high / very low values — ✅ Agreed

**What's wrong (simple version)**
Some days have much bigger numbers than normal (e.g., 36,019 steps). A textbook rule (IQR / "box-plot fence") calls these "outliers" and many tutorials delete them. Should we?

**Project rule:** we remove a value only if it is **impossible**, never just because it is **unusual**.

**Step 1 — Are any values impossible? (757 clean days)**

| Check | Limit for "impossible" | Days breaking it |
|---|---|---|
| Steps | > 50,000 | 0 |
| Distance | > 60 km | 0 |
| Calories | > 6,000 | 0 |
| Very active minutes | > 300 (5 h hard effort) | 0 |
| Calories on a full day | < 1,200 | 0 |
| Steps per km (stride) | outside ~1,000 – 2,000 | 0 (range 1,038 – 1,872) |

→ **Nothing impossible.** Low steps-per-km days (≈ 1,040) belong to runner 8877689391 — running strides are longer, so fewer steps per km. That's physics agreeing with the data.

**Step 2 — What the textbook rule would flag**

| Column | Days flagged "high" | Belong to |
|---|---|---|
| TotalSteps (> 20,127) | 17 | 5 users (8877689391 alone: 8) |
| TotalDistance (> 14 km) | 25 | 6 users |
| VeryActiveMinutes (> 102) | 36 | 7 users (5577150313: 11, 8053475328: 9) |
| Calories (> 4,378) | 7 | 3 users |
| Low side (any column) | 0 | — |

The flagged days are **the same few very active people** doing real workouts. Deleting them would erase the "Very Active" segment — exactly the users marketing wants to understand.

**Lowest values are also real:** lowest calories = 1,328 (user 1624580081), whose *normal* day is ~1,446 → a small person with a low resting burn, not an error.

**Step 3 — One special day can still mislead a person's average**
User 1624580081 on 1 May: **36,019 steps, 28 km** (probably an event or long hike) — 4.8× further from their normal than usual. Calories that day (2,690) match a small person walking 28 km, so it's real.
But it pulls their **monthly average** from 4,974 (median) up to 5,986 → it would move them from **Sedentary** to **Low active**. 4 users change segment depending on mean vs median.

**Solution**
1. **Keep every value** — no deletions, no capping.
2. For each person's **typical day** (used for segmentation), use the **median** (the middle day), which one special day can't pull. Show the mean too where helpful (e.g., total effort).
3. Charts with long tails (steps, distance) use box plots or medians so a few big days don't squash the rest.
4. Note the one odd day: 6117666160 on 21 Apr — highest calories (4,900), 19,542 steps, and half its breakdown missing (P7 group B). Keep, but mention if it shows up in a top-days chart.

**How we'll check**
- Row count unchanged (757)
- Segments are built from per-person median steps

---

## P9 · Some users have very few clean days — ✅ Agreed

**What's wrong (simple version)**
After cleaning, most people have 3–4 weeks of good days, but a few have only 2–3. Judging someone's "typical day" from 2 days is like rating a restaurant after one bite.

**Evidence (clean days per person, after P2–P4)**

| Clean days | People |
|---|---|
| 1 – 6 | **2** |
| 7 – 14 | 3 |
| 15 – 20 | 5 |
| 21 – 25 | 4 |
| 26 – 31 | 19 |

The people at the bottom — and **why** they have so few days:

| Person | Days in raw file | Not worn | Partial | Clean days | Story |
|---|---|---|---|---|---|
| 4057192912 | 4 | 1 | 0 | **2** | **Quit after 4 days** |
| 6775888955 | 26 | 10 | 12 | **3** | **Kept the band 26 days but hardly wore it properly** |
| 1927972279 | 31 | 13 | 10 | 7 | Present all month, but only 7 full days |
| 4020332650 | 31 | 16 | 5 | 9 | Same pattern |
| 1844505072 | 31 | 12 | 6 | 12 | Same pattern |

**Why 7 days as the cut-off?** 7 days = one full week, so the person's typical day can include both weekdays and a weekend. The two people below 7 cover only **2 different weekdays** each; 30 of 33 people cover all 7.

**Why it matters — two sides**
- **Activity analysis:** 2–3 days can't describe someone's habits → their "typical day" and segment would be guesswork.
- **Engagement analysis:** these are exactly the **low-engagement / drop-out** users marketing needs to see. Throwing them away would hide the problem.

**Solution**
1. Add flag `low_data_user` = Yes for people with **< 7 clean days** (4057192912, 6775888955).
2. **Exclude** them from per-person activity profiles and activity segments (typical steps, active minutes, sleep profile).
3. **Keep** them everywhere in day-level charts and in the **engagement analysis** (`wear_log`, non-wear days, drop-outs).
4. New user-level column `clean_day_share` = clean days ÷ 31 → feeds an **engagement tier** for the dashboard, e.g.:
   - **Consistent** (≥ 80% of days clean)
   - **Irregular** (25–80%)
   - **Barely using** (< 25% or quit early)

*(Exact cut-offs to be fixed in feature engineering.)*

**How we'll check**
- `low_data_user` = Yes for exactly 2 people
- Activity segments cover 31 people; engagement page covers all 33

---

## P10 · Missing calendar days (people who stopped) — ✅ Agreed

**What's wrong (simple version)**
33 people × 31 days = 1,023 possible days, but the file has only 940. **83 days have no row at all.**

**Evidence**
- **0 gaps in the middle** of anyone's month. **All 83 missing days come after a person's last day** → these are people who **stopped**, not random skipped days.
- **12 people stopped before 12 May:**

| When they stopped | People | Dates |
|---|---|---|
| **Early** (7+ days before the end) | **4** | 15 Apr · 29 Apr · 30 Apr · 1 May |
| **In the final week** | **8** | 7 May ×2 · 9 May · 10 May ×2 · 11 May ×3 |

- ⚠️ The final-week group is **uncertain**: 6 of them stopped on 9–11 May, just before the data export. They may simply not have **synced** their band before the export — we can't call them drop-outs with confidence.
- **People counted per week shrinks:** week 1: 33 → week 2: 32 → week 3: 32 → week 4: 29 → last days: 26.

**Why it matters**
1. **Filling missing days** (with 0 or an average) would invent data — 0 would fake laziness, an average would fake activity.
2. **Hidden trap — changing crowd:** a "steps per week" trend line averages over *whoever is still there*. If less active people leave, the average rises even though **nobody changed**. (People who stopped have typical steps of 7,810 vs 8,475 for those who stayed.) It's like a class average rising because weak students left, not because anyone studied more.

**Solution**
1. **Never fill** missing days.
2. In `wear_log`, mark them `stopped`.
3. User-level columns:
   - `last_date`, `days_in_study`
   - `stopped_early` = Yes if the last day is 7+ days before 12 May (**4 people**) → real drop-outs
   - `stopped_final_week` = Yes for the 8 uncertain cases (shown separately, not called drop-outs)
4. **Trend charts:** always show "number of users" under each week, **and** draw the main trend line using only people present in every week (so the crowd doesn't change).

**How we'll check**
- No new rows created (still 757 clean rows)
- `stopped_early` = Yes for 4 people; `stopped_final_week` = Yes for 8

---

## P11 · Tidy the columns + final cleaning order — ✅ Agreed

**What's wrong (simple version)**
Column names are long and mixed-style (`VeryActiveMinutes`, `ModeratelyActiveDistance`), two columns are useless, some numbers carry computer noise (20.3999996185303 km), and the user ID is stored as a number even though it's really a **name tag**.

### 1 · Drop

| Column | Why |
|---|---|
| TrackerDistance | Incomplete version of TotalDistance (P6) |
| SedentaryActiveDistance | 1.46 km in the whole month — meaningless (P7) |

### 2 · Rename + fix types (one simple naming style: lowercase_with_underscores, units in the name)

| Old | New | Type / fix |
|---|---|---|
| Id | `user_id` | **Text**, not number — nobody should ever add or average IDs |
| ActivityDate | `date` | Real date (P1) |
| TotalSteps | `steps` | Whole number |
| TotalDistance | `distance_km` | Round to 2 decimals |
| VeryActiveMinutes | `very_active_min` | Blank on 7 `breakdown_missing` days (P7) |
| FairlyActiveMinutes | `fairly_active_min` | " |
| LightlyActiveMinutes | `lightly_active_min` | " |
| SedentaryMinutes | `sedentary_min_raw` | "raw" = **don't chart directly** (P5) |
| VeryActiveDistance | `very_active_km` | 2 decimals; shares only (P7) |
| ModeratelyActiveDistance | `moderate_active_km` | " |
| LightActiveDistance | `light_active_km` | " |
| LoggedActivitiesDistance | `logged_km` | 2 decimals (P6) |
| Calories | `calories` | Whole number |

### 3 · Add (day-level helper columns)

| New column | How | From |
|---|---|---|
| `active_min` | very + fairly + lightly active minutes | P5 — main measure |
| `movement_hours` | hours with ≥ 1 step (hourly file) | P4 |
| `day_of_week`, `is_weekend` | from `date` | Weekday patterns |
| `week_no` | 1–5 from 12 Apr | Trend charts (P10) |
| `sleep_tracked` | Yes if clean sleepDay has that date | P5 |
| `sedentary_awake_min` | sedentary on sleep-tracked days, blank otherwise | P5 |
| `breakdown_missing` | Yes on 7 days | P7 |
| `logged_workout` | logged_km > 0 | P6 |

**User-level columns** (`non_wear_days`, `clean_day_share`, `low_data_user`, `stopped_early`, `stopped_final_week`, `logs_workouts`, typical/median steps…) do **not** go in the daily table — they go in the **user_profile** table built after all 6 files are cleaned. One table = one level of detail.

### 4 · Cleaning order (steps depend on each other)

| Step | Action | Rows |
|---|---|---|
| 1 | Load; convert dates (P1) | 940 |
| 2 | Compute `movement_hours` from hourly file | 940 |
| 3 | **Build `wear_log`** from the raw rows (33 × 31 grid: worn / not_worn / partial / last_day / stopped) — *before* anything is removed | — |
| 4 | Remove each person's last day (P2) | 907 |
| 5 | Remove days with < 100 steps (P3) | 830 |
| 6 | Remove days with < 10 movement hours, except the 7 broken-hourly days (P4) | 757 |
| 7 | Blank the breakdown on the 7 broken days; add `breakdown_missing` (P7) | 757 |
| 8 | Add `sleep_tracked`, `sedentary_awake_min` — *after sleepDay is cleaned* (P5) | 757 |
| 9 | Drop / rename / round / add helper columns (P6, P11) | 757 |
| 10 | Save `daily_clean.csv` and `wear_log.csv` | — |

### Final outputs of this file

| Table | Rows | Level |
|---|---|---|
| `daily_clean.csv` | **757** | one person, one day |
| `wear_log.csv` | **1,023** (33 × 31) | one person, one calendar day — engagement page |

**How we'll check**
- 757 rows, 33 users, no duplicate (user_id, date)
- No column names with capitals; no TrackerDistance / SedentaryActiveDistance
- `user_id` is text; distances have ≤ 2 decimals
- `wear_log` status counts: worn 757 · not_worn 77 · partial 73 · last_day 33 · stopped 83 (total 1,023)

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | P1 agreed — convert date with explicit month/day/year format, rename to `date` |
| 2026-09-30 | P2 agreed — remove each person's final recorded day (not just 12 May) |
| 2026-09-30 | P3 agreed — option B: count non-wear days per user, save `wear_log`, then remove days with < 100 steps. Charging = *likely* cause, not proven |
| 2026-09-30 | P4 agreed — `movement_hours` (hours with ≥ 1 step) replaces `wear_minutes`; keep days with ≥ 10 movement hours; keep 7 broken-hourly days in daily |
| 2026-09-30 | P5 agreed — option B: `sleep_tracked` flag + `sedentary_awake_minutes` (sleep-tracked days only); active minutes & steps are main measures; no sitting-vs-sleep correlation claims |
| 2026-09-30 | P6 agreed — TotalDistance only; drop TrackerDistance; logged distance → `logged_workout` flags (3 users, 31 days) |
| 2026-09-30 | P7 agreed — 7 days with missing effort breakdown: blank the 4 minute + 4 effort-distance columns, flag `breakdown_missing`; keep steps/distance/calories |
| 2026-09-30 | P8 agreed — keep all values (none impossible); per-person typical day = **median**; charts use medians / box plots |
| 2026-09-30 | P9 agreed — `low_data_user` (< 7 clean days, 2 people): out of activity profiles/segments, kept in engagement analysis; add `clean_day_share` for engagement tiers |
| 2026-09-30 | P10 agreed — never fill missing days; mark `stopped` in wear_log; `stopped_early` (4) vs `stopped_final_week` (8, uncertain); trend charts show users per week + fixed-crowd trend line |
| 2026-09-30 | P11 agreed — drop 2 columns, snake_case names with units, `user_id` as text, 2-decimal km, day-level helpers only (user-level → user_profile), fixed 10-step cleaning order; outputs `daily_clean.csv` (757) + `wear_log.csv` (1,023) |
