# Prompt: Generate the Strava Fitness Analytics Dashboard

You are a senior data-visualisation designer and Streamlit/Plotly developer. Design and build an **interactive, multi-page analytics dashboard** for the project below. Use the data description exactly as given — table names, column names, category values and numbers are real.

---

## 1. Business context

- **Audience:** a Strava marketing / product manager (non-technical).
- **Business problem:** Strava has tracker data on users' activity, sleep and body metrics but no clear view of which kinds of users it has, how their habits differ, or which tracking features they actually use — so marketing is one-size-fits-all.
- **Objective:** segment users by activity level and tracking consistency, profile each segment's activity, timing, sleep and feature use, and turn this into **marketing recommendations: which segment to target, with what message, promoting which feature, at what time.**

## 2. About the data

- Public Fitbit tracker dataset: **33 users, 12 Apr – 12 May 2016** (31 days). 18 raw CSVs → 6 used → cleaned into the tables below.
- No activity types (no "running/cycling" labels): effort is measured by intensity levels, distance and step-free effort.
- Small sample → show sample size (n) on charts; use **medians** for "typical" values; say "linked with", never "causes"; no health/medical labels.

## 3. Clean tables (data model)

Join key everywhere: `user_id` (text) + `date`.

### 3.1 `daily_master` — one row per user per valid day (757 rows, 33 users)
| Column | Type | Meaning |
|---|---|---|
| user_id, date | text, date | keys |
| day_of_week, is_weekend, week_no (1–5) | category, bool, int | time dimensions |
| steps | int | daily steps |
| distance_km | float | total distance |
| very_active_min, fairly_active_min, lightly_active_min | int (blank on 7 days) | minutes per effort level |
| active_min | int | very + fairly + lightly (main activity measure) |
| mvpa_min | int | very + fairly (moderate-to-vigorous exercise) |
| calories | int | calories burned |
| movement_hours | int | hours (0–24) with ≥ 1 step |
| goal_10k_met | bool | steps ≥ 10,000 |
| share_very_km, share_moderate_km, share_light_km | float | share of distance by effort |
| sedentary_awake_min | int (blank unless sleep tracked) | awake sitting time |
| sleep_tracked, breakdown_missing, logged_workout | bool | flags |
| sleep_last_night_* / sleep_tonight_* | various | joined sleep for the same / next date |
| hr_avg, hr_resting_est, hr_peak, minutes_hr_above_100 | float | joined heart rate (12 users) |

### 3.2 `hourly_clean` — one row per user per hour (17,987 rows)
user_id, datetime, date, hour (0–23), day_of_week, is_weekend, **time_of_day** (Night 0–4 · Morning 5–11 · Afternoon 12–16 · Evening 17–21 · Late 22–23), steps, calories, intensity (0–180), stepless_effort (bool), workout_hour (bool: intensity ≥ 60).

### 3.3 `sleep_nights` — one row per user per wake-up date (410 rows, 24 users; 384 reliable nights)
user_id, date (wake-up date), night_minutes_asleep, night_hours_asleep, night_minutes_in_bed, sleep_efficiency (0–1), minutes_awake_in_bed, restless_minutes, awake_minutes, night_pieces, bedtime, wake_time, bedtime_hrs_after_6pm, nap_minutes, took_nap, **sleep_category** (< 6 h · 6–7 h · 7–9 h · > 9 h), reliable_night, incomplete_night, capped_session, long_sleep, is_weekend_morning.

### 3.4 `wear_log` — one row per user per calendar day (1,023 rows = 33 × 31)
user_id, date, day_of_week, week_no, **wear_status** (worn 757 · not_worn 77 · partial 73 · last_day 33 · stopped 83), is_worn.

### 3.5 `user_profile` — one row per user (33 rows)
| Group | Columns |
|---|---|
| Coverage | days_in_study, last_date, clean_days, clean_day_share, non_wear_days, low_data_user, low_sleep_data_user, low_hr_data_user |
| Activity (medians) | typical_steps, typical_active_min, typical_mvpa_min, typical_distance_km, typical_calories, weekly_mvpa_min, goal_10k_rate, peak_activity_hour |
| **Segments** | **activity_segment** (Sedentary < 5k · Low active 5–7.5k · Somewhat active 7.5–10k · Active 10k+ steps), **meets_activity_guideline** (≥ 150 MVPA min/week), **week_pattern** (Weekend-active · Weekday-active · Steady), **routine_consistency** (Very regular · Normal · Irregular), **activity_trend** (Rising · Stable · Falling), **preferred_workout_time** (Morning · Afternoon · Evening · Late · None) |
| Engagement | **engagement_tier** (Consistent · Irregular · Barely using), stopped_early, stopped_final_week, **sleep_adoption_level** (Never · Tried · Regular · Consistent), logs_weight, logs_workouts, n_logged_days, features_used (0–3) |
| Sleep (16 users) | typical_sleep_hours, typical_sleep_efficiency, typical_bedtime, typical_wake_time, **bedtime_group** (Early < 10:30 PM · Typical · Late > 12:30 AM), bedtime_regularity, nap_rate, restless_sleeper |
| Body (8 users) | bmi, weight_kg, **bmi_category** (WHO), n_weight_logs, manual_share, weight_habit |
| Heart (12 users) | typical_resting_hr, typical_hr_minutes_above_100 |

### 3.6 `user_body_profile` (8 rows) and `weight_logs_clean` (67 rows)
BMI/weight per user and per entry; is_manual (typed vs smart scale).

## 4. Real numbers (use for KPI cards and realistic visuals)

| KPI | Value |
|---|---|
| Users · clean days | 33 · 757 |
| Typical daily steps | ≈ 8,758 |
| Typical active minutes | ≈ 271 |
| Days hitting 10k steps | ≈ 40% |
| Users meeting exercise guideline | 18 of 31 (58%) |
| Wear rate | ≈ 81% (757 / 940) |
| Engagement tiers | Consistent 20 · Irregular 7 · Barely using 6 |
| Drop-outs | 4 early + 8 uncertain (final week) |
| Activity segments (31 users) | Sedentary 5 · Low active 5 · Somewhat active 10 · Active 11 |
| Week pattern | Weekend-active 16 · Weekday-active 11 · Steady 4 |
| Activity trend | Rising 7 · Stable 12 · Falling 12 |
| Preferred workout time | Morning 13 · Afternoon 9 · Evening 8 · Late 0 · None 3 |
| Peak activity hour | 6 PM (5–7 PM busiest); wake ≈ 7:02 AM; bedtime ≈ 11:13 PM |
| Typical night sleep | 7 h 13 min; efficiency 94% |
| Sleep categories (384 nights) | < 6 h: 86 · 6–7 h: 78 · 7–9 h: 189 · > 9 h: 31 |
| Bedtime groups (16 users) | Early 4 · Typical 8 · Late 4 |
| Sleep adoption (33) | Never 9 · Tried 8 · Regular 4 · Consistent 12 |
| Feature use | Weight logging 8 (24%) · workout logging 3 (9%) |
| Features used (0/1/2/3) | 7 · 18 · 7 · 1 users (more features ↔ more steps & wear days) |
| BMI (8 users) | Normal 3 · Overweight 4 · Obese 1; median 26.4 |
| Heart-rate check | effort minutes vs elevated-HR minutes correlation 0.5 |

## 5. Pages (11)

1. **Home** — business question, 2 KPI rows (activity; sleep & engagement) with sparklines + delta vs group, key findings, navigation cards.
2. **Activity** — segment sizes, segment × guideline, violin of steps by segment, segment profile table, light vs MVPA mix (100% stacked), distance share by effort, weekday-vs-weekend dumbbell per user, step-free workouts callout, sunburst segment → guideline → tier.
3. **Timing** — 24-hour radial clock of activity, day × hour heatmap, hourly steps line, preferred workout time bar, time-of-day small multiples by segment.
4. **Sleep** — sleep KPIs, histogram with 7–9 h band shaded, sleep categories, efficiency per user, **sleep timeline (Gantt of nights: bedtime → wake)**, weekend vs weekday sleep, naps, within-person activity ↔ sleep comparison. Banner: "24 users tracked sleep; profiles use 16".
5. **Engagement & Retention** — **wear calendar** (user × date coloured by wear_status), retention curve, wear rate by week (fixed cohort + users per week), non-wear by weekday, engagement tier × activity segment heatmap, activity-trend slope chart (falling users highlighted), feature-adoption Sankey/funnel, features used vs steps.
6. **Body & Heart** — BMI categories, weight-logging habit (manual vs scale donut), effort vs elevated-HR scatter. Banner: "small samples: weight 8, heart rate 12 users".
7. **Personas** — clickable persona matrix (4 activity segments × 3 engagement tiers with counts) → persona card (size, traits, message, timing, feature to promote) + radar profile.
8. **User Explorer** — pick a user → profile card, GitHub-style activity calendar, daily steps vs group median, sleep per night.
9. **Conclusion** — insight cards with confidence badge (High/Medium/Low by n); each has an **expandable arrow "Evidence" section** (numbers, mini chart, n, link to page) and a recommendation (action · target segment · timing · feature · KPI to track); limitations box; next steps.
10. **Ask AI** — Gemini chatbot (details in §8).
11. **About the Data** — source, 6 of 18 files used and why, cleaning summary, limitations.

## 6. Filters & interactivity

- Global filters in **one row at the top of every page**, remembered across pages: activity segment (multi-select pills), engagement tier (pills), day type (All/Weekdays/Weekends toggle), date range slider. Filter chips + **Reset** button; a line "Showing X users · Y days"; warning when < 3 users remain.
- **Click-to-filter:** clicking or lasso-selecting marks in a chart filters the other charts on the page.
- **Per-chart slicers** wherever useful: metric switch (steps / active min / calories), statistic (median / mean), group-by (segment / tier / week pattern), time grain (day / week).

## 7. Chart rules

- Legend whenever there are 2+ series; hover tooltips on every chart (value + n).
- Every chart has a **"Show data"** expander with its table.
- Bars start at zero; one y-axis per chart (use a metric switch, not dual axes); donut only for ≤ 3 parts, otherwise bars.
- Chart titles state the finding (e.g., "Activity peaks at 6 PM"); subtitles show n.
- Consistent colour meaning on every page: activity segments = one ordered blue scale (light Sedentary → dark Active); engagement tiers = one ordered orange scale; unordered groups = fixed colour-blind-safe categorical order; wear status = status colours (worn green, partial amber, not worn orange-red, stopped grey) always with labels; heatmaps = single-hue scale.

## 8. Ask AI page (Gemini)

- `st.chat_input` / `st.chat_message`, streamed answers, history in session state, "Clear chat" button, starter-question buttons, 3 suggested follow-ups per answer.
- Knowledge: all project plan documents (cleaning plan, feature engineering, EDA plan, dashboard design, conclusions) as system context, plus **function calling** to safe data functions (KPI lookup, segment summary, user lookup, filtered counts) so numbers come from the clean tables.
- Handles vague questions: restates ("Did you mean…?"), asks one clarifying question when needed; aware of the current filters.
- Guardrails: project topics only; says "not in our data" rather than guessing; cites the source; no health advice.
- API key from `st.secrets` / environment variable (never hard-coded); friendly message if missing.

## 9. Tech stack

Python · Streamlit multipage app (`Home.py` + `pages/`) · Plotly · pandas · `@st.cache_data` loaders reading the processed CSVs · Google Gemini API (`google-genai`).

## 10. Visual theme

[TO BE DECIDED — describe colour mood, light/dark mode, fonts and branding here.]

## 11. What to produce

[Choose one: (a) a visual mock-up of each page · (b) the full Streamlit code · (c) a page-by-page layout spec.] Keep the layout clean: KPI cards on top, main charts in the middle, detail and "So what?" takeaway at the bottom of each page.
