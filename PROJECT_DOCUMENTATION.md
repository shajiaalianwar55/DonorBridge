# DonorBridge — Final Project Documentation

**Course deliverable compilation:** relational database design, normalization rationale, transactional and reporting queries, application layer, reproducibility, and submission checklist.

---

## 1. Project summary

DonorBridge models a **blood and transplant coordination–style** domain in **PostgreSQL**: hospitals, patients, donors, differentiated **blood vs organ requests**, donations and **blood units**, **organ offers**, **match candidates**, **transplants**, and an **audit trail** for a natural-language assistant. The codebase includes:

- **DDL & seed**: `database/schema.sql`, `database/seed.sql`
- **Reporting layer**: predefined **`report_*` views** in `database/queries_reports.sql` (plus illustrative inline SQL examples)
- **Applications**: Streamlit prototype (`prototype/`), chatbot backend + Flask UI (`Chatbot/`), optional FastAPI bridge (`integration/`)
- **Design artifacts**: `relational-schema-3nf.html`, `erd-viewer.html`

---

## 2. Database design overview

### 2.1 Core entities (operational)

| Area | Tables | Role |
|------|--------|------|
| Sites | `hospital` | Registration / care centers |
| People | `patient`, `donor` | Persons of interest; donors tied to a hospital |
| Clinical context | `medical_record` | Diagnosis, severity, **hemoglobin**, etc.; 1:M from `patient` |
| Demand | `request` | Unified request row (`BLOOD` or `ORGAN`); FK to patient + hospital |
| Request specialization | `blood_request_details`, `organ_request_details` | **Exclusive** subtype: each `request_id` has at most one subtype row consistent with `request.request_type` (enforced at load time by seed/application; Postgres does not permit CHECK to reference sibling rows). |
| Supply — blood chain | `blood_donation`, `blood_unit` | Donation episodes and derived units |
| Inventory footprint | `blood_inventory_location` | **3NF footprint** — site × blood group staging record (no denormalized “available count” stored in DDL; availability is counted from **`blood_unit`** where `unit_status = 'AVAILABLE'`) |
| Supply — organ | `organ_offer` | Offers linked to donors |
| Fulfillment | `match_candidate`, `transplant` | Candidate links request to blood unit OR organ offer; transplant optional completion |

### 2.2 Audit / assistant subsystem

| Table | Role |
|-------|------|
| `chat_session` | Anchors a conversation to a `hospital_id` and role |
| `chat_message` | Individual user/bot utterances |
| `sql_template` | Named intent/template catalog (seeded via `database/chatbot_sql_template_seed.sql`) |
| `intent_detection` | Which template/classification applies to each user message (**FK → `sql_template`**) |
| `query_execution_log` | Parameter JSON, execution status, row counts (no redundant template FK in current DDL; template known via intent chain) |

The view **`report_assistant_audit_trail`** joins audit tables for governance dashboards.

---

## 3. Normalization process (1NF → 3NF)

### 3.1 First normal form (1NF)

- All attributes are **atomic** (scalar types: text, integers, timestamps, decimals).
- Repeating groups (multiple blood requests, donations, organs) are **not** flattened into repeating columns — they appear as **their own rows** in child tables (`blood_request_details`, `blood_donation`, `blood_unit`, etc.).

### 3.2 Second normal form (2NF)

- Every **non-key** attribute depends on the **whole** primary key of its table (no partial dependencies on compound keys across the schema; primary keys are single-column identities or natural PK such as `request_id` where appropriate).

### 3.3 Third normal form (3NF)

Elimination of transitive and redundant thematic dependencies:

| Design choice | 3NF justification |
|---------------|-------------------|
| **`request` + subtype tables** | Blood-specific facts (`blood_group_required`, `units_required`, `required_by`) and organ-specific facts (`organ_type_required`, etc.) depend on **`request_id`**, not on each other. Keeping them separate avoids nullable “wide” rows and redundancy. Subtype exclusivity (**blood vs organ**) is preserved by business rules / seed parity. |
| **`blood_inventory_location` vs unit counts** | Storing **`available_units_summary`** as a persisted aggregate beside live units creates **update anomalies** whenever a unit moves status. Operational stock is projected from **`blood_unit`** joins (donation → donor → hospital) consistent with **`report_available_blood_units_by_site`**. Location rows encode **staging footprint** rather than authoritative counts (see DDL comments). |
| **`medical_record` separate from `patient`** | A patient may have evolving clinical rows (updated_at); diagnosis/severity/Hb facts do not belong duplicated on `patient` or repeated per request line. |
| **`match_candidate` XOR blood vs organ linkage** | A check constraint ties `match_type` to either **`blood_unit_id`** or **`organ_offer_id`** nullable pattern, enforcing a single modality per candidate row rather than overloaded columns mixing semantics. |

**Reference artifact:** Detailed narrative and diagrams are consolidated in **`relational-schema-3nf.html`** alongside this repository’s DDL.

---

## 4. Constraints, triggers, and data integrity highlights

From **`database/schema.sql`** (non-exhaustive):

- **`patient` / `donor` age** bounds (`CHECK`).
- **`request`**: modality `IN ('BLOOD','ORGAN')`, **urgency 1–5**, open-text `status` (seed uses statuses such as **`OPEN`**; applications use **`ILIKE '%OPEN%'`** where relevant).
- **`blood_unit`** **expiry vs donation**: **trigger `tr_blood_unit_expiry_ge_donation`** insists `expiry_date >= donation_date` (PostgreSQL does not permit subqueries inside `CHECK`; trigger encodes temporal integrity).
- **Referential integrity** via `REFERENCES … ON DELETE RESTRICT CASCADE`/`SET NULL` consistent with stewardship (prevent orphan transplants).

---

## 5. Scripts and reproducible load order

Execute **in pgAdmin**, **psql**, or CI — always same sequence:

| Step | File | Purpose |
|:----:|------|---------|
| 1 | `database/schema.sql` | Drop/create tables, FKs, trigger |
| 2 | `database/seed.sql` | Populate ≥ minimum rows required by assignment scenarios |
| 3 | `database/queries_reports.sql` | `CREATE OR REPLACE VIEW report_*`; safe to rerun |
| 4 | `database/chatbot_sql_template_seed.sql` | Insert `sql_template` rows (`ON CONFLICT DO NOTHING`) for assistant logging |

Rollback **by restoring from backup or re-running** schema + seeds (destructive DDL at top of schema file).

Env var for applications: **`DATABASE_URL`** (`postgresql://user:password@host:port/dbname`).

---

## 6. Queries and reporting surface

### 6.1 View catalog (`database/queries_reports.sql`)

Each view carries a **`COMMENT ON VIEW`** documenting intent.

| View | Business question answered (summary) |
|------|--------------------------------------|
| `report_open_requests_by_hospital` | Open-style counts **by hospital** and modality (`BLOOD` / `ORGAN`), max urgency among open rows |
| `report_available_blood_units_by_site` | **COUNT** of AVAILABLE units attributable to donor registration hospital × blood_group |
| `report_blood_need_vs_supply` | Total **units needed** across open/planned blood requests per ABO vs **approx global** AVAILABLE count for that group |
| `report_organ_offer_pipeline` | Organ **procurement backlog** excerpts |
| `report_match_and_transplant_status` | Match pipeline through optional **transplant** episode |
| `report_assistant_audit_trail` | **Governance replay**: chat message → detected template/intent lineage → execution log |

### 6.2 Ad hoc illustrative SQL (same file)

A block **`/* … */`** at bottom of **`queries_reports.sql`** contains commented examples (**Q1–Q5**): high-risk OPEN requests, anemia+blood demand, deferred donors, transplant window, aggregated intent executions. These are instructional — adjust predicates (e.g. execution status literals) when copying into live tooling.

---

## 7. Application layer (submission scope)

### 7.1 Streamlit prototype (`prototype/streamlit_app.py`)

- **Reports** tab → `pd.DataFrame` over `SELECT * FROM report_*` views.
- **Hospitals** / **Patients** tabs → parameterized **SELECT / INSERT / UPDATE / DELETE**.
- **Assistant** tab → imports **`chatbot_backend`** from `Chatbot/`; Postgres-backed rule-based intents; **`chat_session` / audit** inserts.
- Theme: **`prototype/.streamlit/config.toml`** + injected CSS (**Care Clarity** palette, teal primary; form outlines for accessibility).

See **`prototype/README.md`**.

### 7.2 Chatbot (`Chatbot/`)

- **Direct PostgreSQL** (`psycopg2`): no reliance on **`integration/pg_api.py`** for default operation.
- **Flask SPA** `/static` chat UI **`api.py`**; optional standalone **`streamlit run app.py`** (`Chatbot/.streamlit/config.toml`).
- **Smoke**: `Chatbot/smoke_test.py`.

See **`Chatbot/README.md`** and **`database/chatbot_sql_template_seed.sql`**.

### 7.3 Integration API (`integration/pg_api.py`) — optional

Read-only parameterized FastAPI endpoints for dashboards or tooling; **`uvicorn integration.pg_api:app`** from repo root (`PYTHONPATH` includes package `integration`). Not required for core submission if Streamlit + DB suffice.

---

## 8. Security and submission hygiene

| Topic | Recommendation |
|-------|----------------|
| Credentials | **`prototype/.env` is gitignored**; commit only **`.env.example`**. Rotate DB password if accidentally exposed |
| Hosted demo | Use **minimal-privilege DB user** or read-only replicas for **public-facing** demos; Streamlit Cloud does **not** host Postgres — supply external `DATABASE_URL` |
| Data | Course seed is **synthetic**; replace with de-identified data only under proper governance |

---

## 9. Deliverables checklist (finalize submission)

Submit or attach per instructor requirements:

- [ ] **DDL:** `database/schema.sql`
- [ ] **Data:** `database/seed.sql`
- [ ] **Views + query doc:** `database/queries_reports.sql`
- [ ] **Chat audit seed:** `database/chatbot_sql_template_seed.sql`
- [ ] **Normalization / design narrative:** **`relational-schema-3nf.html`**, **`erd-viewer.html`**
- [ ] **This compilation:** **`PROJECT_DOCUMENTATION.md`** (+ root **`README.md`**)
- [ ] **UI:** **`prototype/`** Streamlit (+ optional **`Chatbot/`**)
- [ ] **Source control:** Tag or release ZIP matching GitHub **`main`**; confirm **`.env` absent** from archive

Optional extras: **`integration/`**, recorded demo video link, **`Chatbot/smoke_test.py`** output screenshot.

---

## 10. Repository reference

**Public repository:** https://github.com/shajiaalianwar55/DonorBridge  

**Suggested citation line (reports / slide decks):**

> DonorBridge — PostgreSQL healthcare resource coordination prototype with 3NF schema, analytic views, Streamlit prototype, and optional chatbot-assisted reporting (repository link above).

---

*Document version: aligns with coursework structure for database design, normalization, queries, and final deliverables. Adjust section numbering or wording to match instructor rubric if required.*
