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


@st.cache_data
def get_airline_list() -> list:
    conn = get_db_connection()
    df = pd.read_sql_query(
        """
        SELECT AIRLINE_CODE
        FROM flights
        GROUP BY AIRLINE_CODE
        HAVING COUNT(*) >= 10000
        ORDER BY AIRLINE_CODE
        """,
        conn,
    )
    return df["AIRLINE_CODE"].tolist()


# -----------------------------------------------------------------------------
# Page Header
# -----------------------------------------------------------------------------
st.title(" Flight Delay Analysis Dashboard")
st.markdown(
    """
    Interactive exploration of **3 million US flight records** from the
    Bureau of Transportation Statistics (BTS), 2019–2023.
    
    ---
     *Built with Python, SQLite, pandas, scikit-learn, and Streamlit.
     Source code on GitHub.*
    ---

    Use the controls in the sidebar to filter the data.
    """
)


# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    selected_airline = st.selectbox(
        "Select Airline",
        options=["All Airlines"] + get_airline_list(),
    )


# -----------------------------------------------------------------------------
# Metrics row
# -----------------------------------------------------------------------------
def build_metrics_query(airline_code: str) -> str:
    where = "WHERE DEP_DELAY IS NOT NULL AND ARR_DELAY IS NOT NULL"
    if airline_code != "All Airlines":
        where += f" AND AIRLINE_CODE = '{airline_code}'"
    return f"""
SELECT
    COUNT(*) AS total_flights,
    ROUND(AVG(CASE WHEN ARR_DELAY >= 15 THEN 1.0 ELSE 0.0 END) * 100, 2) AS delay_rate,
    ROUND(AVG(DEP_DELAY), 2) AS avg_dep_delay
FROM flights
{where};
"""

metrics_df = run_query(build_metrics_query(selected_airline))
col1, col2, col3 = st.columns(3)
col1.metric("Total Flights", f"{int(metrics_df['total_flights'][0]):,}")
col2.metric("Delay Rate (%)", f"{metrics_df['delay_rate'][0]:.1f}%")
col3.metric("Avg Departure Delay", f"{metrics_df['avg_dep_delay'][0]:.1f} min")


# -----------------------------------------------------------------------------
# First chart: average departure delay by day of week
# -----------------------------------------------------------------------------
st.header("Average Departure Delay by Day of Week")

def build_day_of_week_query(airline_code: str) -> str:
    where = "WHERE DEP_DELAY IS NOT NULL"
    if airline_code != "All Airlines":
        where = f"WHERE DEP_DELAY IS NOT NULL AND AIRLINE_CODE = '{airline_code}'"
    return f"""
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
{where}
GROUP BY day_num, day_of_week
ORDER BY day_num;
"""

day_df = run_query(build_day_of_week_query(selected_airline))

chart_title = "Average Departure Delay by Day of Week (US BTS, 2019-2023)"
if selected_airline != "All Airlines":
    chart_title += f" ({selected_airline})"

# Render the chart with matplotlib
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(day_df["day_of_week"], day_df["avg_dep_delay"], color="steelblue", edgecolor="white")
ax.set_xlabel("Day of Week")
ax.set_ylabel("Average Departure Delay (minutes)")
ax.set_title(chart_title)
ax.grid(axis="y", alpha=0.3)

# Add value labels on top of bars
for i, value in enumerate(day_df["avg_dep_delay"]):
    ax.text(i, value + 0.15, f"{value:.1f}", ha="center", fontsize=10)

st.pyplot(fig)


# -----------------------------------------------------------------------------
# Second chart: average departure delay by month
# -----------------------------------------------------------------------------
def build_monthly_query(airline_code: str) -> str:
    where = "WHERE DEP_DELAY IS NOT NULL"
    if airline_code != "All Airlines":
        where += f" AND AIRLINE_CODE = '{airline_code}'"
    return f"""
SELECT
    CAST(strftime('%m', FL_DATE) AS INTEGER) AS month_num,
    CASE strftime('%m', FL_DATE)
        WHEN '01' THEN 'Jan'
        WHEN '02' THEN 'Feb'
        WHEN '03' THEN 'Mar'
        WHEN '04' THEN 'Apr'
        WHEN '05' THEN 'May'
        WHEN '06' THEN 'Jun'
        WHEN '07' THEN 'Jul'
        WHEN '08' THEN 'Aug'
        WHEN '09' THEN 'Sep'
        WHEN '10' THEN 'Oct'
        WHEN '11' THEN 'Nov'
        WHEN '12' THEN 'Dec'
    END AS month_name,
    ROUND(AVG(DEP_DELAY), 2) AS avg_dep_delay
FROM flights
{where}
GROUP BY month_num, month_name
ORDER BY month_num;
"""

st.header("Average Departure Delay by Month")

month_df = run_query(build_monthly_query(selected_airline))

monthly_title = "Average Departure Delay by Month"
if selected_airline != "All Airlines":
    monthly_title += f" ({selected_airline})"

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.plot(
    month_df["month_name"],
    month_df["avg_dep_delay"],
    marker="o",
    linewidth=2,
    markersize=8,
    color="darkblue",
)
ax2.fill_between(month_df["month_name"], month_df["avg_dep_delay"], alpha=0.2, color="darkblue")
ax2.set_ylabel("Average Departure Delay (minutes)")
ax2.set_title(monthly_title)
ax2.grid(alpha=0.3)

for i, value in enumerate(month_df["avg_dep_delay"]):
    ax2.text(i, value + 0.15, f"{value:.1f}", ha="center", fontsize=10)

st.pyplot(fig2)