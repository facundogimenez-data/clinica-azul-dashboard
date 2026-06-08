# Clínica Azul — Dashboard & Automation

![n8n](https://img.shields.io/badge/n8n-EA4B71?style=flat&logo=n8n&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=flat&logo=telegram&logoColor=white)
![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=flat&logo=whatsapp&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

## ⚠️ Production case study — confidentiality note

This project started as a **real reporting solution for a healthcare clinic**, originally
built in Google Sheets + Apps Script. The client's data (patients, appointments, staff)
**cannot be shared publicly for GDPR / healthcare-confidentiality reasons**.

What you'll find in this repo is a **2026 re-architecture and reconstruction**: the same
three reporting areas the clinic relied on — appointment management, resource evaluation,
and patient satisfaction — rebuilt from scratch on a modern stack (Streamlit + MySQL +
Docker + n8n + AI), running against an anonymized demo dataset (synthetic patient codes,
fictional names, ages, and comments — no real names, dates, or contact data).

> **Note on language:** the original clinic, spreadsheet, and dashboard were run in
> Spanish (the clinic is based in Barcelona). For this public portfolio reconstruction,
> the UI, demo data, and documentation have all been translated to English — the
> "Clínica Azul" name is kept as the brand identity of the demo clinic.

## Why the upgrade

The original Sheets/Apps Script setup worked, but it was static, fully manual to update,
and offered no automation around the clinic's two biggest operational pains:
**appointment no-shows** and **slow, unstructured feedback review**. The 2026 version
turns the report into a **live system**:

- A **real-time dashboard** instead of a spreadsheet that needed manual refreshes
- **Automated WhatsApp/Telegram reminders** the day before each appointment — directly
  targeting no-show reduction, the #1 lever for clinic revenue and schedule efficiency
- **AI-powered sentiment analysis** on patient satisfaction comments, so the team sees
  *why* patients are happy or unhappy without reading every single comment by hand

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **n8n** | Automation: appointment reminders (multi-channel) + AI sentiment analysis pipeline |
| **MySQL** | Structured storage for appointments, staff, patients, and satisfaction surveys |
| **OpenAI (GPT-4.1 mini) + AI Agent** | Classifies patient comments as positive / neutral / negative with a confidence score |
| **Streamlit** | Live dashboard across the three reporting areas |
| **Telegram Bot API + Evolution API (WhatsApp)** | Multi-channel appointment reminders |
| **Docker / docker-compose** | One-command local deployment (MySQL + dashboard) |

## Architecture overview

```
 Scheduling system ──► MySQL (appointments, staff, patients, surveys)
                              │
            ┌─────────────────┼──────────────────────┐
            ▼                 ▼                      ▼
   n8n: Appointment    n8n: Sentiment          Streamlit Dashboard
   Reminders           Analysis (AI Agent)     (3 tabs: appointments,
   (Telegram +         classifies survey       resources, satisfaction)
   WhatsApp daily)     comments → MySQL
```

### 1. n8n — `Clínica Azul - Appointment Reminders`

Runs daily and looks for appointments scheduled in the next 24 hours that haven't
received a reminder yet:

1. **Schedule – Daily Reminder Check** — Triggers every morning
2. **MySQL – Get Appointments Needing Reminder** — Pulls appointments with
   `status = 'scheduled'` and `reminder_sent_at IS NULL` in the next 24 h
3. **Build Reminder Message** — Formats a friendly, personalized reminder per appointment
4. **Send Reminder (Telegram)** + **Send Reminder (WhatsApp – Evolution API)** —
   Delivers the reminder through both channels
5. **MySQL – Mark Reminder Sent** — Updates `reminder_sent_at` so the same
   appointment is never reminded twice

This single workflow directly targets the no-show rate — the metric with the
biggest impact on a clinic's daily schedule and revenue — without adding any
manual work for reception staff.

### 2. n8n — `Clínica Azul - Sentiment Analysis`

Runs on a schedule and processes any satisfaction survey comment that hasn't
been classified yet:

1. **Schedule – Sentiment Analysis Check** — Triggers periodically
2. **MySQL – Get Surveys Pending Sentiment** — Pulls comments with `sentiment IS NULL`
3. **AI Agent – Sentiment Classifier** (OpenAI GPT-4.1 mini) — Classifies each
   comment as `positive` / `neutral` / `negative` and assigns a `-1.0`–`1.0` score
4. **Parse Sentiment Output** — Extracts the structured result from the agent's response
5. **MySQL – Update Survey Sentiment** — Persists the classification for reporting

This turns free-text feedback — previously something someone had to read one by
one — into a structured signal the dashboard can summarize and trend over time.

### 3. Streamlit Dashboard

A single app with three tabs, each covering one of the original report's areas:

- **Appointment management** — Total appointments, attendance, no-show rate, reminder
  coverage, and breakdown by service type
- **Medical resources** — Per-professional workload, attendance rate, and
  occupancy — useful for staffing and capacity planning decisions
- **Patient satisfaction** — Average score, sentiment breakdown (powered by the n8n +
  AI pipeline above), and a feed of recent comments with their classification

## Running it locally

```bash
git clone https://github.com/facundogimenez-data/clinica-azul-dashboard.git
cd clinica-azul-dashboard
cp .env.example .env
docker compose up --build
```

This spins up a MySQL instance pre-loaded with the schema and synthetic demo
data ([`db/schema.sql`](db/schema.sql)), and the dashboard at `http://localhost:8501`.

To run the dashboard alone against your own MySQL instance:

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

## Deploying to EasyPanel

See [`DEPLOY.md`](DEPLOY.md) for a step-by-step guide using `docker-compose.prod.yml`
(self-contained MySQL + dashboard stack, seeded automatically from `db/schema.sql`).

## Project structure

| Path | Purpose |
|------|---------|
| [`app/app.py`](app/app.py) | Streamlit dashboard (appointments, resources, satisfaction) |
| [`db/schema.sql`](db/schema.sql) | MySQL schema + synthetic demo data |
| [`docker-compose.yml`](docker-compose.yml) / [`Dockerfile`](Dockerfile) | One-command local deployment |
| `n8n workflows` | `Clínica Azul - Appointment Reminders` and `Clínica Azul - Sentiment Analysis` (described above; not exported here as they reference live credentials) |

## Author

**Facundo Gimenez** — [LinkedIn](https://www.linkedin.com/in/facundo-r-gimenez/) | [GitHub](https://github.com/facundogimenez-data)
