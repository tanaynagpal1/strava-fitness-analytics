# 04 · minuteSleep — Cleaning Notes

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning) · **Role:** Bedtime, wake time, naps, restlessness · **Status: ✅ ALL 8 PROBLEMS AGREED — plan complete**

> Running log of problems and solutions. We use this file only to **derive** sleep-timing columns — its minute rows are summarised to one row per sleep session, then one row per night.

---

## File at a glance

| Item | Value |
|---|---|
| What it is | One row = one minute of one sleep session, marked 1 = asleep, 2 = restless, 3 = awake |
| Size | 188,521 rows × 4 columns |
| People | 24 (same people as sleepDay) |
| Time range | 11 Apr 2016 20:48 → 12 May 2016 09:56 |
| Sleep sessions (`logId`) | 459 — exactly equal to the total of sleepDay's TotalSleepRecords ✅ |
| Blanks | None |
| Exact duplicate rows | **543** |

### Columns

| Keep (renamed) | Meaning |
|---|---|
| Id · date → `datetime` · value → `sleep_state` · logId → `session_id` | All 4 needed |

---

## Problem summary

| # | Problem | Solution in one line | Status |
|---|---|---|---|
| M1 | Exact duplicate rows (one whole night copied twice) | Remove duplicates | ✅ Agreed |
| M2 | Date-time stored as text; some times end in :30 seconds | Convert; round down to the minute | ✅ Agreed |
| M3 | Codes 1/2/3 are not readable | Map to asleep / restless / awake | ✅ Agreed |
| M4 | Sessions cross midnight | Assign each session to its **wake-up date** | ✅ Follows S3 |
| M5 | Naps vs main sleep not labelled | Main = longest session per wake date; sessions within 2 h of it = same night; rest = naps | ✅ Follows S4 |
| M6 | Minute-level data too detailed for analysis | Summarise to session, then to night → `sleep_nights.csv` | ✅ Follows S9 |
| M7 | 4 sessions last exactly 961 min (recording limit) | Flag `capped_session`; exclude from duration stats (see sleepDay S6) | ✅ Follows S6 |
| M8 | Minutes asleep differ slightly from sleepDay on 14 nights | Use minuteSleep as the source; accept small gaps | ✅ Agreed |

---

## M1 · Exact duplicate rows — ✅ Agreed

**Evidence** 543 rows are exact copies. They are **one entire night copied twice**: user 4702921684, session 11573168523, 6 May 9:10 PM → 7 May 6:12 AM (1,086 rows = 543 × 2). The **same night is also duplicated in sleepDay** (S1: 4702921684 on 7 May) → one export glitch hit both files. No case where the same minute has two *different* values.

**Solution** Remove exact duplicates → 187,978 rows.

**How we'll check** No (Id, datetime) appears twice; that session's length now matches sleepDay's time in bed.

---

## M2 · Text date-time and :30 seconds — ✅ Agreed

**Evidence** 126,714 times end in :00 and 61,807 end in :30 (e.g., "2:47:30 AM"). Each **session is consistent** — 159 of 459 sessions are entirely at :30, none are mixed. So the :30 is just where that session's recording started.

**Solution** Convert with the explicit format (follows P1), then round **down** to the whole minute. Safe: after rounding, **0** duplicate minutes and **0** overlapping sessions.

---

## M3 · Codes not readable — ✅ Agreed

**Evidence** Values: 1 = 172,480 min, 2 = 14,023 min, 3 = 2,018 min.

**Solution** Map 1 → `asleep`, 2 → `restless`, 3 → `awake`.

---

## M4 · Sessions cross midnight — ✅ Follows S3

**Evidence** 254 of 459 sessions start on one date and end on the next (e.g., 11 PM → 7 AM).

**Solution** Give each session a `wake_date` = date of its last minute. This matches sleepDay exactly (time in bed matches **100%** using wake date vs 37% using start date — see sleepDay S3).

---

## M5 · Naps vs main sleep — ✅ Follows S4

**Evidence** Session start times cluster at 8 PM–3 AM (the normal night), but **39 sessions start between 9 AM and 7 PM** (naps). Shortest session = 60 minutes; no tiny fragments.

**Solution**
- For each person + wake_date: the **longest** session = `main_sleep`.
- Another session starting/ending **within 2 hours** of the main sleep = `night_piece` (broken night — woke up and went back to bed). **18** such pieces.
- Everything else = `nap`. **30** naps from 9 people.
- **Bedtime** = start of the earliest night session; **wake time** = end of the latest night session. Naps never set bedtime.

**How we'll check** 459 sessions = 410 main + 18 night pieces + 31 naps; bedtimes mostly fall in the evening/night. (See sleepDay S4 for the evidence.)

---

## M6 · Summarise to a usable level — ✅ Follows S9

**Step A — one row per session**

| Column | How |
|---|---|
| `sleep_start`, `sleep_end` | first / last minute |
| `minutes_asleep`, `minutes_restless`, `minutes_awake` | count of each state |
| `session_type` | main_sleep / nap (M5) |

**Step B — one row per person per night (wake_date)**

| Column | Why it matters |
|---|---|
| `bedtime` (clock time of main sleep start) | Sleep timing pattern; late-sleeper segment |
| `wake_time` (clock time of main sleep end) | Morning routine → best time for morning notifications |
| `restless_minutes`, `awake_minutes` | Sleep quality beyond sleepDay's totals |
| `nap_minutes`, `took_nap` | Nap behaviour |

**Bedtime tip for later:** a bedtime of 11:30 PM and one of 12:30 AM are only 1 hour apart, but as clock numbers they are 23.5 and 0.5. For averages, measure bedtime as "hours after 6 PM" (11:30 PM → 5.5, 12:30 AM → 6.5).

**Result:** joins onto the daily master table using (Id, wake_date).

---

## M8 · Small differences vs sleepDay — ✅ Agreed

**Evidence** Time in bed matches sleepDay on **100%** of nights. Minutes asleep match on **96.6%**; on the other 14 nights minuteSleep counts **1–22 more** asleep minutes (median 4).

**Solution** minuteSleep is our source for night sleep (it's the detailed record). Keep sleepDay totals only as reference. A 4-minute gap changes nothing.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | M4–M7 follow sleepDay S3, S4, S9, S6 |
| 2026-09-30 | M1, M2, M3, M8 agreed — drop the duplicated night; explicit format + round down to minute; map 1/2/3 → asleep/restless/awake; minuteSleep is the source for night sleep |
| 2026-10-01 | Phase 2 check — session split recounted: 410 main · 18 night pieces · 31 naps (see sleepDay S4 log) |
