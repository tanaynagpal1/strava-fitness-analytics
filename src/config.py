"""Project paths and every threshold agreed in Phase 1.

Each constant points to the decision it comes from (see the Cleaning Notes folder),
so a reviewer can trace any number in the dashboard back to the plan.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "Data Source"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

RAW_FILES = {
    "daily": "dailyActivity_merged.csv",
    "hourly_steps": "hourlySteps_merged.csv",
    "hourly_calories": "hourlyCalories_merged.csv",
    "hourly_intensities": "hourlyIntensities_merged.csv",
    "sleep_day": "sleepDay_merged.csv",
    "minute_sleep": "minuteSleep_merged.csv",
    "weight": "weightLogInfo_merged.csv",
    "heartrate": "heartrate_seconds_merged.csv",
}

# ---------------------------------------------------------------- dates (P1, H2, S2, M2, W3, R2)
# American month/day/year — always explicit, never guessed (Indian day/month trap).
DATE_FMT = "%m/%d/%Y"
DATETIME_FMT = "%m/%d/%Y %I:%M:%S %p"
STUDY_START = "2016-04-12"
STUDY_END = "2016-05-12"
STUDY_DAYS = 31

# ---------------------------------------------------------------- daily valid-day rules
MIN_STEPS_WORN = 100            # P3: fewer steps = band not worn
MIN_MOVEMENT_HOURS = 10         # P4: hours with >= 1 step
MIN_PROFILE_DAYS = 7            # P9 / S8 / R6: 7-day rule for per-person profiles
STOP_EARLY_DAYS = 7             # P10: last day 7+ days before the end = real drop-out

# ---------------------------------------------------------------- hourly
STEPLESS_MIN_INTENSITY = 30     # H9: effort with zero steps
WORKOUT_HOUR_INTENSITY = 60     # F2: an hour of real exercise
TIME_OF_DAY = [                 # F1: (label, first hour, last hour)
    ("Night", 0, 4), ("Morning", 5, 11), ("Afternoon", 12, 16), ("Evening", 17, 21), ("Late", 22, 23),
]

# ---------------------------------------------------------------- sleep
NAP_GAP_HOURS = 2               # S4: pieces within 2 h of the main sleep = same night
MIN_NIGHT_ASLEEP = 180          # S5: under 3 h = incomplete night
CAPPED_SESSION_MIN = 961        # S6: recording limit glitch
LONG_SLEEP_MIN = 600            # S6: > 10 h = long sleep (kept)
DAYTIME_START_HOURS = range(9, 20)  # S5 kind A: a main session starting 9 AM - 7:59 PM is a nap
RESTLESS_EFFICIENCY = 0.85      # S7
SLEEP_CATEGORIES = [(0, 360, "< 6 h"), (360, 420, "6–7 h"), (420, 540, "7–9 h"), (540, 10_000, "> 9 h")]

# ---------------------------------------------------------------- heart rate
HR_MIN_MINUTES = 600            # R3: >= 10 h of readings

# ---------------------------------------------------------------- weight
BMI_CATEGORIES = [(0, 18.5, "Underweight"), (18.5, 25, "Normal"), (25, 30, "Overweight"), (30, 100, "Obese")]  # W7 WHO
WEIGHT_HABIT_LOGS = 10

# ---------------------------------------------------------------- segments (F3–F7)
STEP_SEGMENTS = [(0, 5000, "Sedentary"), (5000, 7500, "Low active"), (7500, 10000, "Somewhat active"), (10000, 10**9, "Active")]
SEGMENT_ORDER = [s for _, _, s in STEP_SEGMENTS]
MVPA_GUIDELINE_WEEK = 150       # F4 WHO guideline
GOAL_STEPS = 10_000
ENGAGEMENT_CONSISTENT = 0.80    # F5
ENGAGEMENT_BARELY = 0.25
TIER_ORDER = ["Consistent", "Irregular", "Barely using"]
WEEK_PATTERN_HIGH = 1.10        # F6
WEEK_PATTERN_LOW = 0.90
TREND_CHANGE = 0.10             # F6: +/-10 % between month halves
MONTH_SPLIT = "2016-04-27"      # first half = 12-26 Apr, second half = 27 Apr onwards
BEDTIME_EARLY = 4.5             # F7: hours after 6 PM -> 10:30 PM
BEDTIME_LATE = 6.5              # 12:30 AM
PERSONA_ORDER = ["Committed Movers", "On-and-Off Movers", "Daily Strollers", "Slipping Starters", "Fading Users"]   # F8 (Q29)
