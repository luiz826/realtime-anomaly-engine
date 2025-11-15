import streamlit as st
import pandas as pd
import plotly.express as px
from anomaly_engine import database # <-- IMPORT DATABASE MODULE

# --- Page Config ---
st.set_page_config(
    page_title="Real-Time Anomaly Detection Engine",
    layout="wide"
)

st.title("🚀 Real-Time E-Commerce Anomaly Detection Engine")

# --- Data Loading Functions ---
# @st.cache_data is replaced by st.cache_resource for connections
@st.cache_resource
def get_conn():
    return database.get_db_connection()

@st.cache_data(ttl=10)
def load_metrics():
    """Loads the last 10 minutes of metrics data."""
    conn = get_conn()
    query = """
        SELECT window_start, status_code, event_count
        FROM metrics
        WHERE window_start >= NOW() - INTERVAL '10 minutes'
        ORDER BY window_start ASC;
    """
    df = pd.read_sql(query, conn)
    return df

@st.cache_data(ttl=10)
def load_llm_alerts():
    """Loads the last 5 LLM-generated alerts."""
    conn = get_conn()
    try:
        query = """
            SELECT timestamp, insight_text
            FROM llm_alerts
            ORDER BY timestamp DESC
            LIMIT 5;
        """
        df = pd.read_sql(query, conn)
        return df
    except: # Table might not exist yet
        return pd.DataFrame(columns=["timestamp", "insight_text"])

# --- Dashboard Layout ---
# (The layout code is identical to before)
metrics_df = load_metrics()
if metrics_df.empty:
    st.info("Waiting for data... (Make sure producer.py and processor.py are running)")
else:
    fig = px.bar(
        metrics_df, x="window_start", y="event_count", color="status_code",
        title="Events per 30-sec Window",
        color_continuous_scale=px.colors.sequential.Bluered_r,
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("🚨 Live LLM-Generated Anomaly Insights")
alerts_df = load_llm_alerts()
if alerts_df.empty:
    st.success("✅ No anomalies detected recently.")
else:
    for index, row in alerts_df.iterrows():
        with st.expander(f"**Anomaly @ {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}**", expanded=True):
            st.markdown(row['insight_text'])

# --- Auto-Refresh ---
import time
time.sleep(5)
st.rerun()