# 09 · Streamlit Dashboard Design

**Project:** Strava Fitness Data Analytics · **Phase:** 1 (Planning, step 1.7) · **Status:** 🟡 Proposed — to be agreed

> What the dashboard shows, page by page: its purpose, filters, KPI cards, charts (linked to the EDA questions Q1–Q30), colours and rules.
> Audience: a **Strava marketing / product manager** — non-technical, wants "who, when, what to do".

---

## 1 · Design principles

| # | Principle | In practice |
|---|---|---|
| 1 | **Every page answers one business question** | Page title = the question; a "So what?" box at the bottom = the marketing takeaway |
| 2 | **Headline first, detail after** | KPI cards on top → main charts → detail / data table |
| 3 | **Chart titles state the finding** | "Activity peaks at 6 PM", not "Steps by hour" |
| 4 | **Always show the sample size** | Subtitle like "16 users · 384 nights"; banner on small-sample pages |
| 5 | **Medians, not averages** | Tooltips say "typical (median)" |
| 6 | **Same colour = same thing on every page** | A segment keeps its colour everywhere, even when filters remove others |
| 7 | **Fast** | App reads small pre-cleaned CSVs (cached); never the raw 2.5 M-row heart-rate file |
| 8 | **Honest language** | "linked with", never "causes"; no health labels |

---

## 2 · Tech choices

| Item | Choice | Why |
|---|---|---|
| App framework | **Streamlit multipage app** (`Home.py` + `pages/` folder) | Built-in page navigation in the sidebar |
| Charts | **Plotly** | Hover tooltips, zoom, legends out of the box; works with Streamlit |
| Data | Processed CSVs from Phase 2 (`daily_master`, `hourly_clean`, `sleep_nights`, `wear_log`, `user_profile`, …) | Small, clean, fast |
| Speed | `@st.cache_data` on every loader | Data loads once, pages switch instantly |
| Theme | `.streamlit/config.toml` light theme + a matching Plotly template (dark-mode colours defined too) | Consistent look |

---

## 3 · Global filters (one row at the top of each page)

| Filter | Options | Applies to |
|---|---|---|
| **Activity segment** | All · Sedentary · Low active · Somewhat active · Active | All pages |
| **Engagement tier** | All · Consistent · Irregular · Barely using | All pages |
| **Day type** | All · Weekdays · Weekends | Activity, Timing, Sleep |
| **Date range** | 12 Apr – 11 May 2016 | Day-level pages |

- Filters sit in **one row above the charts** (not scattered); the sidebar holds only page navigation + "About the data".
- A small line under the filters shows what's selected: *"Showing 10 users · 243 days"*.
- User-level exclusions from cleaning (e.g., `low_data_user`) are applied automatically, with a note.

---

## 4 · Pages

### Page 0 · 🏠 Home — "How are Strava users moving, sleeping and engaging?"

| Block | Content |
|---|---|
| Intro | 2-line business objective + data note (33 Fitbit users, 12 Apr – 12 May 2016) |
| **KPI row 1 — Activity** | Typical daily steps (≈ 8,758) · Typical active minutes (≈ 271) · 10k-goal days (≈ 40%) · Meet exercise guideline (18/31) |
| **KPI row 2 — Sleep & engagement** | Typical sleep (7 h 13 m) · Sleep efficiency (94%) · Wear rate (≈ 81%) · Consistent users (20/33) |
| Key findings | 3–4 one-line findings with a link to their page |
| Navigation cards | One card per page with its question |

### Page 1 · 🏃 Activity — "Who are our users and how active are they?" (EDA T1, T3)

| Chart | Type | EDA Q |
|---|---|---|
| Users per activity segment | Bar (ordered Sedentary → Active) | Q1 |
| Segment × meets exercise guideline | Stacked bar | Q2 |
| Daily steps by segment | Box plot | Q3 |
| Segment profile table | Table (steps, MVPA, distance, calories, sleep, engagement per segment) | Q3 |
| Active-time mix: light vs moderate-vigorous | 100% stacked bar per segment | Q11 |
| Distance share by effort | Stacked bar | Q12 |
| Weekday vs weekend steps per user | Dumbbell | Q4, Q8 |
| Step-free workouts | Callout card + example day | Q13 |

**So what:** segment sizes and what each segment needs.

### Page 2 · ⏰ Timing — "When are users active?" (EDA T2)

| Chart | Type | EDA Q |
|---|---|---|
| Average steps by hour | Line (single series) | Q6 |
| Effort by hour | Separate line chart (**never** a second axis on the steps chart) | Q6 |
| Day × hour | **Heatmap** (one-hue scale) | Q7 |
| Preferred workout time | Bar | Q9 |
| Time-of-day pattern by segment | Small multiples (one mini-chart per segment) | Q10 |

**So what:** the best days/hours for notifications and campaigns, per segment.

### Page 3 · 😴 Sleep — "How well do users sleep?" (EDA T4, T5)

| Block | Type | EDA Q |
|---|---|---|
| KPI row | Typical sleep · efficiency · % nights 7–9 h · % nights < 6 h | — |
| Night-sleep distribution | Histogram with the 7–9 h band shaded | Q15 |
| Sleep categories | Bar | Q15 |
| Efficiency per user | Box plot per user (restless sleeper visible) | Q16 |
| Bedtime & wake time per user | Range / strip plot | Q17 |
| Weekend vs weekday sleep | Paired box plot | Q18 |
| Naps | Bar (nap rate per user) | Q19 |
| Activity ↔ sleep (within each person) | Paired comparison: active days vs quiet days | Q20–Q22 |

Banner: *"Sleep data: 24 users tracked sleep; profiles use 16 users with 7+ reliable nights."*
**So what:** sleep-feature messages (short sleepers, irregular bedtimes, wind-down timing).

### Page 4 · 📈 Engagement & Retention — "Who keeps using the device, and who is slipping?" (EDA T6)

| Chart | Type | EDA Q |
|---|---|---|
| **Wear calendar** (person × date) | Heatmap coloured by wear status (worn / partial / not worn / stopped) with legend + labels | Q23 |
| Wear rate by week | Line (fixed crowd) + "users present" under each week | Q24 |
| Non-wear by weekday | Bar | Q24 |
| Engagement tiers | Bar | — |
| Engagement tier × activity segment | Heatmap table (counts) | Q25 |
| Activity trend (1st vs 2nd half of month) | Slope chart; **falling** users highlighted | Q26 |
| Feature adoption funnel | Funnel / bar (sleep · weight · workout logging) | Q27 |
| Feature depth vs typical steps | Bar | Q27 |

**So what:** churn-risk groups, charging reminders, "try a second feature" campaign.

### Page 5 · ⚖️ Body & Heart — supporting evidence (EDA T3, T7)

Banner: *"Small samples: weight 8 users, heart rate 12 users — descriptive only."*

| Chart | Type | EDA Q |
|---|---|---|
| BMI categories (WHO) | Bar | Q28 |
| Weight-logging habit (entries per user, manual vs scale) | Bar | Q28 |
| Effort minutes vs elevated-heart-rate minutes | Scatter — "the band's data is trustworthy" | Q14 |
| Elevated-HR minutes by segment | Box plot | Q14 |

### Page 6 · 🎯 Personas & Recommendations — "What should Strava do?" (EDA T8)

| Block | Content | EDA Q |
|---|---|---|
| **Persona matrix** | 4 activity segments × 3 engagement tiers — count in each cell, click/select a cell | Q29 |
| Persona cards | Name, size, key traits (steps, workout time, sleep, features used), **recommended message, timing, feature to promote** | Q29 |
| Top recommendations | Table: recommendation · supporting finding · affected users · confidence | Q30 |

### Page 7 · 🔍 User Explorer (drill-down)

| Block | Content |
|---|---|
| User picker | Select one `user_id` |
| Profile card | Segment, engagement tier, typical steps, workout time, sleep profile, features used |
| Their month | Daily steps line (their data highlighted, group median in grey), wear calendar row, sleep per night |

Useful for demos and for checking that personas make sense.

### Page 8 · ℹ️ About the Data

Data source, 6 files used / 10 skipped, cleaning summary (51 problems → key rules), limitations (33 users, 1 month, 2016, no activity types, correlation ≠ cause), link to the cleaning plan.

---

## 5 · Colour system (same meaning on every page)

| Used for | Colour rule | Why |
|---|---|---|
| **Activity segments** (ordered) | One blue scale, light → dark: Sedentary `#86b6ef` · Low `#3987e5` · Somewhat `#1c5cab` · Active `#0d366b` | Ordered groups read naturally as "more = darker" |
| **Engagement tiers** (ordered) | A second one-hue scale in **orange**, light → dark (Barely using → Consistent) | Different family from segments, so the two never get confused |
| **Unordered groups** (time of day, week pattern, bedtime group) | Fixed categorical order: blue `#2a78d6` · orange `#eb6834` · aqua `#1baf7a` · yellow `#eda100` · magenta `#e87ba4` | Colour-blind-safe order; never cycled or regenerated |
| **Wear status** | Status colours with labels: worn `#0ca30c` · partial `#fab219` · not worn `#ec835a` · last day / stopped = greys | "Good / warning / bad" meaning; never used for anything else |
| **Heatmaps** | One blue scale, light (low) → dark (high) | Magnitude |
| **Highlight** | One accent colour for the item in focus, everything else grey | e.g., the selected user in User Explorer |
| Text | Dark grey ink, never coloured text | Readability |

All palettes are checked with a colour-blindness validator in Phase 2 before use.

---

## 6 · Chart rules

| Rule | Why |
|---|---|
| **One y-axis per chart** — never two measures on two axes | Dual axes mislead; use two charts instead |
| **No pie charts**; use bars / stacked bars | Bars are easier to compare |
| Legend whenever there are ≥ 2 series; direct labels when ≤ 4 | Identity never by colour alone |
| Hover tooltips on every chart, showing value + n | Detail on demand |
| Light gridlines, thin bars with small gaps | Clean look |
| Every chart has a **"Show data"** expander with the table behind it | Transparency + accessibility |
| Bar charts start at zero | Honest comparisons |

---

## 7 · Data each page reads

| Page | Tables |
|---|---|
| Home | user_profile, daily_master, sleep_nights |
| Activity | daily_master, user_profile, hourly_clean (step-free workouts) |
| Timing | hourly_clean, user_profile |
| Sleep | sleep_nights, daily_master, user_profile |
| Engagement | wear_log, user_profile, daily_master |
| Body & Heart | user_body_profile, daily_master (hr_* columns), user_profile |
| Personas | user_profile |
| User Explorer | all |
| About | static text |

---

## 8 · Tanay's additions (30 Sep) — analysis, proposed

### 8.1 · New page 9 · 🤖 Ask AI (Gemini chatbot)

| Part | Proposal |
|---|---|
| What it answers | Dashboard & data questions, cleaning decisions (why 6 of 18 files, every P/H/S/M/W/R problem), feature engineering, EDA, insights |
| **Knowledge (docs)** | All plan files (00–09 + conclusions) given to Gemini as background context — ~25k tokens, fits easily, no complex search system needed |
| **Knowledge (numbers)** | A few **safe data functions** Gemini can call (function calling): KPI lookup, segment summary, user profile lookup, filtered counts — so numbers come from our clean tables, not from the AI's memory |
| Vague questions | Starter-question buttons · bot restates "Did you mean…?" · asks one clarifying question when needed · 3 suggested follow-ups after each answer |
| Knows the filters | Current filter selection passed into the question |
| Guardrails | Only project topics · says "not in our data" instead of guessing · cites the source (doc / page / table) · no health advice |
| API key | `st.secrets` / environment variable — **never in code or GitHub**; page shows a friendly setup message if the key is missing |
| UX | `st.chat_input` + `st.chat_message`, streamed answers, chat history in `st.session_state`, "Clear chat" button |
| Cost / limits | Free-tier rate limits → short cooldown; if deployed publicly, add a simple password or per-session limit |

### 8.2 · New page 10 · ✅ Conclusion (insights & recommendations)

| Part | Proposal |
|---|---|
| Insight card | One-line insight + confidence badge (High / Medium / Low, based on n) |
| **Evidence (arrow tab)** | `st.expander` — click the arrow → key numbers, a mini chart, sample size, link to the full page |
| Recommendation | Action · target persona/segment · timing · feature to promote · KPI to track |
| Also | Limitations box; "next steps / A-B tests to validate" |
| Overlap fix | "Top recommendations" moves from Personas → Conclusion; Personas keeps the matrix + persona cards |

**New page order (11):** Home · Activity · Timing · Sleep · Engagement · Body & Heart · Personas · User Explorer · **Conclusion** · **Ask AI** · About

### 8.3 · Interactive filters

| Feature | How |
|---|---|
| Filters **remember** across pages | `st.session_state` |
| Click-to-filter (cross-filtering) | Click / lasso on a Plotly chart → other charts on the page update (`st.plotly_chart(on_select="rerun")`) |
| Modern controls | Multiselect / pills for segments & tiers, segmented control for day type, date slider |
| Filter chips + **Reset** button | Always visible |
| Small-sample guard | Warning when a filter leaves < 3 users |

### 8.4 · Per-chart slicers & unique charts

Per-chart slicers: metric switch (steps / active min / calories), statistic (median / mean), group-by (segment / tier / week pattern), time grain (day / week).

| Page | Unique charts |
|---|---|
| Home | KPI cards with sparklines + delta vs group |
| Activity | Violin / ridgeline of steps by segment · dumbbell weekday vs weekend · beeswarm of users · sunburst (segment → guideline → tier) |
| Timing | **24-hour radial clock** · day × hour heatmap · small multiples |
| Sleep | **Sleep timeline (Gantt of each night)** · histogram with 7–9 h band · weekend slope chart |
| Engagement | **Wear calendar** · **retention curve** · **Sankey** of feature adoption · slope chart of trend |
| Personas | Clickable persona matrix · radar profile per persona (with table) |
| User Explorer | GitHub-style activity calendar · profile vs group |

### 8.5 · Chart rules (confirmed by Tanay)
Legend for 2+ series · hover tooltips everywhere · "Show data" table on every chart · bars start at zero.
**Open:** keep "one y-axis per chart" and "no pie charts"? (recommendation: keep one-axis; allow a donut only for ≤ 3 parts)

---

## Decisions needed

| # | Decision | Proposal |
|---|---|---|
| D1 | Pages | Home · Activity · Timing · Sleep · Engagement · Body & Heart · Personas · User Explorer · About (9) |
| D2 | Filters | Segment, engagement tier, day type, date range — one row at the top of each page |
| D3 | Tech | Streamlit multipage + Plotly + cached processed CSVs |
| D4 | Colours | Section 5 |
| D5 | Chart rules | Section 6 |
| D6 | Optional pages | Keep User Explorer and About? |

---

## Decision log

| Date | Decision |
|---|---|
| 2026-09-30 | D1 agreed — 9 pages + 2 new pages (Ask AI, Conclusion) → 11 pages; interactivity & unique charts requested; themes to be discussed next |
