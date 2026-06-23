"""
Flight Analysis Project - Dashboard Application
Interactive Streamlit app exploring US BTS flight data 2019-2023
"""

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Flight Delay Analysis",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Database path 
# -----------------------------------------------------------------------------
DB_PATH = Path(__file__).parent.parent / "data" / "flights.db"


# -----------------------------------------------------------------------------
# Database connection 
# -----------------------------------------------------------------------------
@st.cache_resource
def get_db_connection():
    """Open a connection to the SQLite database. Cached across reruns."""
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


# -----------------------------------------------------------------------------
# Cached query function
# -----------------------------------------------------------------------------
@st.cache_data
def run_query(query: str) -> pd.DataFrame:
    """Run a SQL query and return the results as a DataFrame. Cached across reruns."""
    conn = get_db_connection()
    return pd.read_sql_query(query, conn)


# -----------------------------------------------------------------------------
# Page Header
# -----------------------------------------------------------------------------
st.title(" Flight Delay Analysis Dashboard")
st.markdown(
    """
    Interactive exploration of **3 million US flight records** from the
    Bureau of Transportation Statistics (BTS), 2019–2023.

    Use the controls in the sidebar to filter the data.
    """
)


# -----------------------------------------------------------------------------
# First chart: average departure delay by day of week
# -----------------------------------------------------------------------------
st.header("Average Departure Delay by Day of Week")

day_of_week_query = """
SELECT
    CASE strftime('%w', FL_DATE)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END AS day_of_week,
    CAST(strftime('%w', FL_DATE) AS INTEGER) AS day_num,
    ROUND(AVG(DEP_DELAY), 2) AS avg_dep_delay
FROM flights
WHERE DEP_DELAY IS NOT NULL
GROUP BY day_num, day_of_week
ORDER BY day_num;
"""

day_df = run_query(day_of_week_query)

# Render the chart with matplotlib
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(day_df["day_of_week"], day_df["avg_dep_delay"], color="steelblue", edgecolor="white")
ax.set_xlabel("Day of Week")
ax.set_ylabel("Average Departure Delay (minutes)")
ax.set_title("Average Departure Delay by Day of Week (US BTS, 2019-2023)")
ax.grid(axis="y", alpha=0.3)

# Add value labels on top of bars
for i, value in enumerate(day_df["avg_dep_delay"]):
    ax.text(i, value + 0.15, f"{value:.1f}", ha="center", fontsize=10)

st.pyplot(fig)