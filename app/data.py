"""Loads the clean tables once and keeps them in memory (cache) for every page."""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"

DATE_COLS = {
    "daily_master":      ["date"],
    "daily_clean":       ["date"],
    "wear_log":          ["date"],
    "hourly_clean":      ["datetime", "date"],
    "sleep_nights":      ["date"],
    "sleep_sessions":    ["start", "end", "wake_date"],
    "weight_logs_clean": ["date"],
    "user_body_profile": ["first_log_date", "last_log_date"],
    "daily_heart_rate":  ["date"],
    "user_profile":      ["first_date", "last_date"],
}
TABLES = list(DATE_COLS)


@st.cache_data(show_spinner="Loading data …")
def load(name: str) -> pd.DataFrame:
    """Read one clean table: user_id stays text (P11), date columns become real dates."""
    return pd.read_csv(DATA / f"{name}.csv", dtype={"user_id": str}, parse_dates=DATE_COLS[name])