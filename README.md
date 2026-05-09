# DonorBridge

Healthcare resource coordination **prototype**: PostgreSQL data model (3NF), seeded demo data, **reporting views**, **Streamlit** UI (reports + CRUD + assistant), optional **rule-based chatbot**, and an optional **read-only HTTP API** over Postgres.

---

## Documentation (final submission)

| Document | Purpose |
|----------|---------|
| [**PROJECT_DOCUMENTATION.md**](PROJECT_DOCUMENTATION.md) | **Full submission doc:** database design, normalization, queries, artifacts, reproducibility |
| [**relational-schema-3nf.html**](relational-schema-3nf.html) | Interactive 3NF relational write-up |
| [**erd-viewer.html**](erd-viewer.html) | ERD visualization (HTML) |
| [**prototype/README.md**](prototype/README.md) | Streamlit install & run |
| [**Chatbot/README.md**](Chatbot/README.md) | Chatbot install, intents, Postgres setup |

---

## Quick setup (PostgreSQL)

Run SQL **in order** against your database (see full detail in **PROJECT_DOCUMENTATION.md** §5):

```text
database/schema.sql
database/seed.sql
database/queries_reports.sql          -- report_* views + commented ad hoc queries
database/chatbot_sql_template_seed.sql -- chatbot audit templates (Assistant / Chatbot logging)
```

Set **`DATABASE_URL`** (see **`prototype/.env.example`**).

**Streamlit (main UI):**

```bash
cd prototype
pip install -r ../requirements-ui.txt
copy .env.example .env    # edit DATABASE_URL
streamlit run streamlit_app.py
```

**Flask chat UI (alternate):**

```bash
cd Chatbot
pip install -r requirements.txt
python api.py             # expects ../prototype/.env for DATABASE_URL
```

**Integration API (optional):** from repo root, `pip install -r integration/requirements.txt`, then:

```bash
uvicorn integration.pg_api:app --host 127.0.0.1 --port 8787
```

---

## Repository

**GitHub:** [shajiaalianwar55/DonorBridge](https://github.com/shajiaalianwar55/DonorBridge)

Secrets (`.env`) are gitignored — use `.env.example` as a template.
