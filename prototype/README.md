# DonorBridge prototype (Streamlit)

Small UI for **reports** against PostgreSQL **`report_*` views**, **basic CRUD** on `hospital`, `patient`, and **`request`** (blood / organ with detail rows), plus an **Assistant** tab — the same rule-based chatbot as `Chatbot/app.py`, embedded here.

## Prerequisites

1. PostgreSQL with `donorbridge` (or any database) populated from the repo DDL and seed:

   ```bash
   psql … -f ../database/schema.sql
   psql … -f ../database/seed.sql
   psql … -f ../database/queries_reports.sql
   psql … -f ../database/chatbot_sql_template_seed.sql
   ```

   The **`queries_reports.sql`** step defines the views consumed by the **Reports** tab.  
   **`chatbot_sql_template_seed.sql`** fills `sql_template` so the **Assistant** tab can log intents (keep the **`Chatbot/`** folder beside `prototype/` on disk).

2. Python 3.10+ recommended.

## Install

From the **`prototype`** directory:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r ../requirements-ui.txt
```

Copy **`.env.example`** to **`.env`** in this folder (or set a system env var):

```bash
copy .env.example .env
```

Edit `.env` and set **`DATABASE_URL`** to your Postgres connection string, for example:

`postgresql://postgres:secret@localhost:5432/donorbridge`

## Run

Still inside **`prototype`**:

```bash
streamlit run streamlit_app.py
```

Theme (teal primary, light background) is set in **`.streamlit/config.toml`** — same care-style tokens as **`Chatbot/static/styles.css`**.

Use the sidebar **Test connection** button if something fails (`DATABASE_URL` missing is the usual culprit).

## Other tools (coursework alternatives)

Instead of Streamlit you could sketch the same workflows with:

- **Power BI / Looker Studio** — query the **`report_*` views** directly.
- **Retool**, **Appsmith**, or **Budibase** — bind forms to Postgres.
- **FlutterFlow / Glide** — expose a REST API over the database first.
- **React / Vue + Express** — custom stack with more setup.

This prototype favors speed: one Python file reads views and submits safe `INSERT`/`UPDATE`/`DELETE` statements.
