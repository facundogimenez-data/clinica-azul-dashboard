"""
Clínica Azul Dashboard
======================
Streamlit + MySQL dashboard for a healthcare clinic. Replaces the original
Google Sheets / Apps Script reporting with a live app fed by:

- Appointment data synced from the clinic's scheduling system
- Automated WhatsApp/Telegram reminders sent via n8n (reduces no-shows)
- Patient satisfaction surveys, scored for sentiment by an n8n + LLM workflow

Covers the same three areas as the original report — appointment management,
medical resource evaluation, and patient satisfaction — with richer,
real-time visualizations.
"""

import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Clínica Azul — Dashboard",
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
    st.header("📅 Gestión de citas")

    total = len(df)
    attended = (df["status"] == "attended").sum()
    no_show = (df["status"] == "no_show").sum()
    cancelled = (df["status"] == "cancelled").sum()
    no_show_rate = (no_show / total * 100) if total else 0
    reminder_coverage = (df["reminder_sent_at"].notna().sum() / total * 100) if total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Citas totales", total)
    col2.metric("Asistencia", attended)
    col3.metric("Tasa de no-show", f"{no_show_rate:.1f}%")
    col4.metric("Cobertura de recordatorios", f"{reminder_coverage:.0f}%")

    st.caption(
        "Los recordatorios se envían automáticamente por WhatsApp/Telegram "
        "(workflow de n8n) ~24 h antes de cada cita — reduce el ausentismo "
        "sin trabajo manual de recepción."
    )

    status_counts = df["status"].value_counts().rename(
        {"attended": "Asistió", "no_show": "No-show", "cancelled": "Cancelada", "scheduled": "Programada"}
    )
    st.bar_chart(status_counts)

    st.subheader("Citas por tipo de servicio")
    service_counts = df.groupby("service_type")["appointment_id"].count().rename("Citas")
    st.bar_chart(service_counts)


def section_resources(df: pd.DataFrame):
    st.header("🩺 Evaluación de recursos médicos")

    by_staff = (
        df.groupby(["staff_name", "staff_role"])
        .agg(
            citas=("appointment_id", "count"),
            asistidas=("status", lambda s: (s == "attended").sum()),
            no_shows=("status", lambda s: (s == "no_show").sum()),
        )
        .reset_index()
    )
    by_staff["tasa_ocupacion"] = (by_staff["asistidas"] / by_staff["citas"] * 100).round(1)

    display = by_staff.rename(
        columns={
            "staff_name": "Profesional",
            "staff_role": "Rol",
            "citas": "Citas asignadas",
            "asistidas": "Atendidas",
            "no_shows": "No-shows",
            "tasa_ocupacion": "Tasa de ocupación (%)",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.bar_chart(by_staff.set_index("staff_name")["tasa_ocupacion"])


def section_satisfaction(surveys: pd.DataFrame):
    st.header("⭐ Satisfacción del paciente")

    if surveys.empty:
        st.info("Todavía no hay encuestas registradas.")
        return

    avg_score = surveys["score"].mean()
    sentiment_counts = surveys["sentiment"].value_counts()
    positive_pct = (sentiment_counts.get("positive", 0) / len(surveys) * 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("Encuestas recibidas", len(surveys))
    col2.metric("Puntuación media", f"{avg_score:.1f} / 5")
    col3.metric("Comentarios positivos", f"{positive_pct:.0f}%")

    st.caption(
        "Cada comentario se clasifica automáticamente como positivo / neutro / "
        "negativo mediante un workflow de n8n con un modelo de lenguaje (análisis "
        "de sentimiento), sin intervención manual."
    )

    sentiment_chart = sentiment_counts.rename(
        {"positive": "Positivo", "neutral": "Neutro", "negative": "Negativo"}
    )
    st.bar_chart(sentiment_chart)

    st.subheader("Comentarios recientes")
    display = surveys[["submitted_at", "service_type", "staff_name", "score", "sentiment", "comment"]].rename(
        columns={
            "submitted_at": "Fecha",
            "service_type": "Servicio",
            "staff_name": "Profesional",
            "score": "Puntuación",
            "sentiment": "Sentimiento",
            "comment": "Comentario",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def main():
    st.title("🦷 Clínica Azul — Dashboard")
    st.caption(
        "Reporting en tiempo real: gestión de citas, evaluación de recursos "
        "médicos y satisfacción del paciente — alimentado por automatizaciones "
        "de n8n y un modelo de datos en MySQL."
    )

    try:
        appointments = load_appointments()
        surveys = load_surveys()
    except Exception as exc:
        st.error(f"No se pudo conectar a la base de datos: {exc}")
        st.info(
            "Configura DB_HOST, DB_PORT, DB_USER, DB_PASSWORD y DB_NAME en un "
            "archivo .env (ver .env.example) y carga el esquema de db/schema.sql."
        )
        return

    if appointments.empty:
        st.warning("No hay citas registradas todavía.")
        return

    tab1, tab2, tab3 = st.tabs(["Gestión de citas", "Recursos médicos", "Satisfacción"])
    with tab1:
        section_appointments(appointments)
    with tab2:
        section_resources(appointments)
    with tab3:
        section_satisfaction(surveys)


if __name__ == "__main__":
    main()
