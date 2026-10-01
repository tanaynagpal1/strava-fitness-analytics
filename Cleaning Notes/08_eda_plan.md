# 08 · EDA Plan — Questions, KPIs & Method

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning, step 1.6) · **Status:** ✅ Agreed (E1–E4)

> What we will explore in Phase 2, in what order, with which columns and charts — and how each answer feeds a **marketing decision**.
> Every question maps back to the business objective: *which segment to target, with what message, promoting which feature, at what time.*

---

## 1 · EDA in 5 layers (the order we work in)

| Layer | Goal | Example |
|---|---|---|
| **L1 · Data overview** | Know what we're standing on | Users per table, days per user, wear rate |
| **L2 · One variable at a time** | Shape of each measure | Distribution of steps, sleep hours, BMI |
| **L3 · Patterns over time** | When things happen | Hour of day, weekday vs weekend, week 1→4 |
| **L4 · Relationships & segments** | Who differs from whom | Segment profiles, activity ↔ sleep, engagement ↔ activity |
| **L5 · Marketing synthesis** | Turn findings into actions | Persona matrix → recommendation per persona |

---

## 2 · Method rules for EDA (from our cleaning decisions)

| # | Rule | Why |
|---|---|---|
| 1 | "Typical" = **median**; spread shown with box plots | One special day can't distort (P8) |
| 2 | **Every person counts once** in person-level charts | Heavy loggers don't dominate (W4) |
| 3 | Show **n (users / days)** on every chart using a subset | Sleep 16–24, weight 8, heart rate 12 users |
| 4 | Trends over weeks use the **fixed crowd** (people present all weeks) + show users per week | Changing-crowd trap (P10) |
| 5 | Activity ↔ sleep: compare each person **with themselves** (their active days vs their quiet days) | Avoids "different people are different" confusion |
| 6 | Sitting time only from `sedentary_awake_min`; never correlate sitting with sleep | Maths-forced relationship (P5) |
| 7 | Hourly table only for time-of-day patterns, never for daily totals | H5 |
| 8 | Language: "linked with", never "causes"; no health labels | Small sample; neutral wording |

---

## 3 · Headline KPIs (dashboard cards)

Values already known from cleaning checks are filled in; the rest are computed in Phase 2.

| Area | KPI | Definition | Known value |
|---|---|---|---|
| Coverage | Users · Days analysed | distinct users · clean days | 33 · 757 |
| Activity | Typical daily steps | median steps (clean days) | ≈ 8,758 |
| Activity | Typical active minutes | median `active_min` | ≈ 271 |
| Activity | 10k-goal hit rate | % days `goal_10k_met` | ≈ 40% |
| Activity | Meets exercise guideline | % users `meets_activity_guideline` | 18 of 31 (58%) |
| Engagement | Wear rate | worn days ÷ days in study | 757 / 940 ≈ 81% |
| Engagement | Consistent users | % `engagement_tier` = Consistent | 20 of 33 (61%) |
| Engagement | Drop-outs | `stopped_early` | 4 of 33 (12%) |
| Sleep | Typical night | median night sleep (reliable) | 7 h 13 min |
| Sleep | Sleep efficiency | median | 94% |
| Sleep | Nights in 7–9 h / under 6 h | % reliable nights | 49% / 22% |
| Sleep | Typical bedtime / wake | median | ≈ 11:13 PM / 7:02 AM |
| Features | Sleep tracking · weight logging · workout logging | % users using | 73% tried (36% consistent) · 24% · 9% |

---

## 4 · Question bank (by theme)

Columns refer to the tables in `07_feature_engineering.md`. **Marketing use** = the decision the answer supports.

### T1 · Who are our users? (segmentation)

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q1 | How are users spread across activity segments? | user_profile: `typical_steps`, `activity_segment` | Histogram + segment bar | Size of each target group |
| Q2 | Do step segments agree with the exercise guideline? | `activity_segment` × `meets_activity_guideline` | Stacked bar / crosstab | Who's under-counted by steps |
| Q3 | How do segments differ (steps, MVPA, distance, calories, sleep, engagement)? | user_profile | Segment profile table / grouped bars | Message per segment |
| Q4 | Weekend-active vs weekday-active vs steady? | `week_pattern` | Bar + dumbbell (weekday vs weekend steps per user) | Weekday vs weekend campaigns |
| Q5 | How regular are people's routines? | `routine_consistency`, steps CV | Bar + strip plot | Habit-building nudges |

### T2 · When are they active? (timing)

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q6 | What does an average day look like hour by hour? | hourly_clean: `hour`, steps, intensity | Line / bar by hour | Best notification hours |
| Q7 | Weekday × hour — when are peaks? | `day_of_week` × `hour` | **Heatmap** | Day-and-time campaign scheduling |
| Q8 | Weekday vs weekend daily activity | daily: `is_weekend` | Box plot | Weekend challenge ideas |
| Q9 | When do people prefer to work out? | user_profile: `preferred_workout_time` | Bar | Personalised reminder times |
| Q10 | Does timing differ by segment? | hourly × `activity_segment` | Small-multiple lines | Segment-specific timing |

### T3 · How hard do they move? (intensity)

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q11 | How is the active day split (light vs moderate-vigorous)? | daily: minute columns | 100% stacked bar per segment | "Turn light activity into workouts" message |
| Q12 | Share of distance by effort | distance shares | Donut / stacked bar | Same |
| Q13 | How common are step-free workouts? | hourly: `stepless_effort` | Bar by user + example day | Promote cycling/swim/gym tracking |
| Q14 | Does the band's effort data agree with heart rate? | daily_master: `mvpa_min` vs `minutes_hr_above_100` | Scatter (n = 12) | Data-trust statement |

### T4 · How do they sleep?

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q15 | How long do people sleep? | sleep_nights: `night_hours_asleep`, `sleep_category` | Histogram + category bar | "22% of nights under 6 h" hook |
| Q16 | How well — efficiency, restlessness, broken nights? | `sleep_efficiency`, `night_pieces` | Box plot per user | Sleep-quality feature |
| Q17 | When do they go to bed / wake, and how regular? | `bedtime_group`, `bedtime_regularity` | Strip / range plot per user | Wind-down / morning message timing |
| Q18 | Do people sleep longer at weekends? | `is_weekend_morning` | Paired box plot | Weekend-recovery content |
| Q19 | Who naps, and when? | `took_nap`, `nap_rate` | Bar | Nap-tracking feature |

### T5 · Activity ↔ sleep (within-person comparisons)

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q20 | After a more active day, do people sleep longer / better that night? | daily_master: `mvpa_min` vs `sleep_tonight_*` | Per-person paired comparison | "Move more, sleep better" — only if the data supports it |
| Q21 | After a short night, are people less active the next day? | `sleep_last_night_*` vs steps | Same | Recovery / rest-day messaging |
| Q22 | Do active segments sleep differently? | segment × sleep profile (16 users) | Grouped box | Cross-feature promotion |

### T6 · Engagement & retention

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q23 | Who wears the band, when? | wear_log: `wear_status` | **Calendar heatmap** (person × date) | The engagement picture at a glance |
| Q24 | When does non-wear happen? (weekday, week 1→4, take-off-and-forget) | wear_log + hourly | Bars + line | Charging reminders, week-2 re-engagement |
| Q25 | Are low-engagement users also less active? | `engagement_tier` × `activity_segment` | Crosstab heatmap | Priority group |
| Q26 | Who is falling off? | `activity_trend`, `stopped_early` | Slope chart (1st vs 2nd half) | Churn-risk alerts |
| Q27 | Feature adoption funnel + "feature depth" | `sleep_adoption_level`, `logs_weight`, `logs_workouts`, `features_used` | Funnel + bar | "Try a second feature" campaign |

### T7 · Body metrics (n = 8)

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q28 | BMI mix and weight-logging habits | user_body_profile | Category bar + log-count bar | Smart-scale / easy-logging feature |

### T8 · Synthesis

| # | Question | Data | Chart | Marketing use |
|---|---|---|---|---|
| Q29 | **Persona matrix:** activity segment × engagement tier — who's in each cell, and what do they need? | user_profile | 4 × 3 grid with counts + key traits | **One recommendation per persona** |
| Q30 | Top 5 recommendations, each backed by a finding | all | Summary table | Final deliverable |

---

## 5 · Deliverables of the EDA (Phase 2)

| Deliverable | Content |
|---|---|
| EDA notebook | Q1–Q30 in order, each with chart + 2–3 line finding |
| Findings table | Finding · evidence (number) · confidence (n) · marketing action |
| Persona sheet | Q29 grid with description per persona |
| Chart set | The charts reused in the Streamlit dashboard (step 1.7) |

---

## Decisions needed

| # | Decision | Proposal |
|---|---|---|
| E1 | EDA layers & order | L1 → L5 as above |
| E2 | Method rules | 8 rules in section 2 |
| E3 | KPI list | Section 3 |
| E4 | Question bank | Q1–Q30 (add / drop any?) |

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | E1–E4 agreed — 5 layers, 8 method rules, KPI list, question bank Q1–Q30 |

  | 2026-10-02 | Phase 2 EDA done (L1–L5) — wear-rate KPI changed to 83.5% (last days excluded); 5 personas (17 · 2 · 3 · 5 · 6); top 5 recommendations in notebook |
