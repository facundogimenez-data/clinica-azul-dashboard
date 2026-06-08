"""
Clinica Azul Dashboard
======================
Streamlit + MySQL dashboard for a healthcare clinic. Replaces the original
Google Sheets / Apps Script reporting with a live app fed by:

- Appointment data synced from the clinic's scheduling system
- Automated WhatsApp/Telegram reminders sent via n8n (reduces no-shows)
- Patient satisfaction surveys, scored for sentiment by an n8n + LLM workflow

Covers the same three areas as the original report — appointment management,
medical resource evaluation, and patient satisfaction — with richer,
real-time visualizations.

Note: the original clinic, spreadsheet, and dashboard were run in Spanish
(the clinic is based in Barcelona). This public reconstruction keeps the
"Clinica Azul" brand name but translates all UI text and demo data to
English for portfolio purposes.
"""

import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Clinica Azul — Dashboard",
    page_icon="🦷",
    layout="wide",
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "3306"),
    "user": os.getenv("DB_USER", "demo_user"),
    "password": os.getenv("DB_PASSWORD", "demo_password"),
    "database": os.getenv("DB_NAME", "clinica_azul_demo"),
}


@st.cache_resource
def get_engine():
    url = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url)


@st.cache_data(ttl=300)
def load_appointments() -> pd.DataFrame:
    query = """
        SELECT
            a.appointment_id,
            a.scheduled_at,
            a.service_type,
            a.status,
            a.reminder_sent_at,
            s.full_name AS staff_name,
            s.role      AS staff_role,
            p.patient_code,
            p.first_name,
            p.last_name,
            p.age_range
        FROM appointments a
        JOIN staff s    ON s.staff_id = a.staff_id
        JOIN patients p ON p.patient_id = a.patient_id
        ORDER BY a.scheduled_at;
    """
    df = pd.read_sql(query, get_engine())
    df["scheduled_at"] = pd.to_datetime(df["scheduled_at"])
    return df


@st.cache_data(ttl=300)
def load_surveys() -> pd.DataFrame:
    query = """
        SELECT
            sv.survey_id,
            sv.score,
            sv.comment,
            sv.sentiment,
            sv.sentiment_score,
            sv.submitted_at,
            a.service_type,
            s.full_name AS staff_name
        FROM satisfaction_surveys sv
        JOIN appointments a ON a.appointment_id = sv.appointment_id
        JOIN staff s        ON s.staff_id = a.staff_id
        ORDER BY sv.submitted_at DESC;
    """
    return pd.read_sql(query, get_engine())


def section_appointments(df: pd.DataFrame):
    st.header("📅 Appointment management")

    total = len(df)
    attended = (df["status"] == "attended").sum()
    no_show = (df["status"] == "no_show").sum()
    cancelled = (df["status"] == "cancelled").sum()
    no_show_rate = (no_show / total * 100) if total else 0
    reminder_coverage = (df["reminder_sent_at"].notna().sum() / total * 100) if total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total appointments", total)
    col2.metric("Attended", attended)
    col3.metric("No-show rate", f"{no_show_rate:.1f}%")
    col4.metric("Reminder coverage", f"{reminder_coverage:.0f}%")

    st.caption(
        "Reminders are sent automatically via WhatsApp/Telegram (n8n workflow) "
        "~24h before each appointment — cutting no-shows without any extra "
        "manual work for reception."
    )

    status_counts = df["status"].value_counts().rename(
        {"attended": "Attended", "no_show": "No-show", "cancelled": "Cancelled", "scheduled": "Scheduled"}
    )
    st.bar_chart(status_counts)

    st.subheader("Appointments by service type")
    service_counts = df.groupby("service_type")["appointment_id"].count().rename("Appointments")
    st.bar_chart(service_counts)


def section_resources(df: pd.DataFrame):
    st.header("🩺 Medical resource evaluation")

    by_staff = (
        df.groupby(["staff_name", "staff_role"])
        .agg(
            appointments=("appointment_id", "count"),
            attended=("status", lambda s: (s == "attended").sum()),
            no_shows=("status", lambda s: (s == "no_show").sum()),
        )
        .reset_index()
    )
    by_staff["occupancy_rate"] = (by_staff["attended"] / by_staff["appointments"] * 100).round(1)

    display = by_staff.rename(
        columns={
            "staff_name": "Staff member",
            "staff_role": "Role",
            "appointments": "Assigned appointments",
            "attended": "Attended",
            "no_shows": "No-shows",
            "occupancy_rate": "Occupancy rate (%)",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.bar_chart(by_staff.set_index("staff_name")["occupancy_rate"])


def section_satisfaction(surveys: pd.DataFrame):
    st.header("⭐ Patient satisfaction")

    if surveys.empty:
        st.info("No surveys recorded yet.")
        return

    avg_score = surveys["score"].mean()
    sentiment_counts = surveys["sentiment"].value_counts()
    positive_pct = (sentiment_counts.get("positive", 0) / len(surveys) * 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("Surveys received", len(surveys))
    col2.metric("Average score", f"{avg_score:.1f} / 5")
    col3.metric("Positive comments", f"{positive_pct:.0f}%")

    st.caption(
        "Each comment is automatically classified as positive / neutral / "
        "negative by an n8n workflow powered by an LLM (sentiment analysis), "
        "with no manual review required."
    )

    sentiment_chart = sentiment_counts.rename(
        {"positive": "Positive", "neutral": "Neutral", "negative": "Negative"}
    )
    st.bar_chart(sentiment_chart)

    st.subheader("Recent comments")
    display = surveys[["submitted_at", "service_type", "staff_name", "score", "sentiment", "comment"]].rename(
        columns={
            "submitted_at": "Date",
            "service_type": "Service",
            "staff_name": "Staff member",
            "score": "Score",
            "sentiment": "Sentiment",
            "comment": "Comment",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def main():
    st.title("🦷 Clinica Azul — Dashboard")
    st.caption(
        "Real-time reporting: appointment management, medical resource "
        "evaluation, and patient satisfaction — powered by n8n automations "
        "and a MySQL data model."
    )

    try:
        appointments = load_appointments()
        surveys = load_surveys()
    except Exception as exc:
        st.error(f"Could not connect to the database: {exc}")
        st.info(
            "Set DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME in a "
            ".env file (see .env.example) and load the schema from db/schema.sql."
        )
        return

    if appointments.empty:
        st.warning("No appointments recorded yet.")
        return

    tab1, tab2, tab3 = st.tabs(["Appointment management", "Medical resources", "Patient satisfaction"])
    with tab1:
        section_appointments(appointments)
    with tab2:
        section_resources(appointments)
    with tab3:
        section_satisfaction(surveys)


if __name__ == "__main__":
    main()
