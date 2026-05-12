-- DonorBridge: business queries & reporting helpers
-- Run after schema.sql + seed.sql. Safe to re-run (views use CREATE OR REPLACE).

BEGIN;

-- ---------------------------------------------------------------------------
-- Report views (reusable in BI tools or the Streamlit prototype)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW report_open_requests_by_hospital AS
SELECT
    h.hospital_id,
    h.name AS hospital_name,
    -- request_type lives on `request`, not `hospital`; LEFT JOIN yields NULL until this hospital has rows there.
    COALESCE(r.request_type, '(no requests yet)') AS request_type,
    COUNT(*) FILTER (WHERE r.status ILIKE '%OPEN%') AS open_count,
    COALESCE(
        MAX(r.urgency_level) FILTER (WHERE r.status ILIKE '%OPEN%'),
        0
    ) AS max_open_urgency
FROM hospital h
LEFT JOIN request r ON r.hospital_id = h.hospital_id
GROUP BY h.hospital_id, h.name, r.request_type
ORDER BY h.name, r.request_type;

COMMENT ON VIEW report_open_requests_by_hospital IS 'OPEN-style requests by hospital and modality (blood vs organ). Hospitals with no requests show (no requests yet) for request_type.';

CREATE OR REPLACE VIEW report_available_blood_units_by_site AS
SELECT
    d.hospital_id,
    h.name AS hospital_name,
    bu.blood_group,
    bu.unit_status,
    COUNT(*) AS unit_count,
    AVG(bu.volume_ml)::INTEGER AS avg_volume_ml
FROM blood_unit bu
JOIN blood_donation bd ON bd.blood_donation_id = bu.blood_donation_id
JOIN donor d ON d.donor_id = bd.donor_id
JOIN hospital h ON h.hospital_id = d.hospital_id
WHERE bu.unit_status = 'AVAILABLE'
GROUP BY d.hospital_id, h.name, bu.blood_group, bu.unit_status
ORDER BY h.name, bu.blood_group;

COMMENT ON VIEW report_available_blood_units_by_site IS 'Operational stock: AVAILABLE units attributable to donor registration hospital.';

CREATE OR REPLACE VIEW report_blood_need_vs_supply AS
SELECT
    br.blood_group_required,
    SUM(br.units_required) AS units_needed_open_blood_requests,
    (
        SELECT COUNT(*)
        FROM blood_unit bu2
        WHERE bu2.blood_group = br.blood_group_required
          AND bu2.unit_status = 'AVAILABLE'
    ) AS approx_available_matching_units_global
FROM request req
JOIN blood_request_details br ON br.request_id = req.request_id
WHERE req.request_type = 'BLOOD'
  AND (req.status ILIKE '%OPEN%' OR req.status ILIKE '%PROPOSED%')
GROUP BY br.blood_group_required
ORDER BY br.blood_group_required;

COMMENT ON VIEW report_blood_need_vs_supply IS 'High-level squeeze check: summed open blood units needed vs AVAILABLE inventory (global matching ABO).';

CREATE OR REPLACE VIEW report_organ_offer_pipeline AS
SELECT
    o.organ_offer_id,
    d.full_name AS donor_label,
    o.organ_type,
    o.availability_status,
    o.retrieval_date::DATE AS retrieval_date_only,
    LEFT(o.medical_clearance, 80) AS clearance_excerpt
FROM organ_offer o
JOIN donor d ON d.donor_id = o.donor_id
ORDER BY o.retrieval_date NULLS LAST;

COMMENT ON VIEW report_organ_offer_pipeline IS 'Procurement-facing organ offer backlog with terse clearance excerpt.';

CREATE OR REPLACE VIEW report_match_and_transplant_status AS
SELECT
    mc.match_id,
    mc.match_type,
    mc.match_status,
    mc.priority_level,
    r.request_id,
    r.status AS request_status,
    mc.compatibility_score,
    t.transplant_id,
    t.transplant_date,
    LEFT(t.surgeon_name, 40) AS surgeon,
    LEFT(COALESCE(t.outcome, '—'), 60) AS outcome_excerpt
FROM match_candidate mc
JOIN request r ON r.request_id = mc.request_id
LEFT JOIN transplant t ON t.match_id = mc.match_id
ORDER BY mc.match_date DESC;

COMMENT ON VIEW report_match_and_transplant_status IS 'Operational bridge from matching through completed transplant episode.';

CREATE OR REPLACE VIEW report_assistant_audit_trail AS
SELECT
    qel.execution_id,
    qel.executed_at,
    cm.sender_type,
    LEFT(cm.message_text, 72) AS message_excerpt,
    st.intent_code,
    qel.execution_status,
    qel.rows_returned,
    qel.param_json
FROM query_execution_log qel
JOIN intent_detection idet ON idet.intent_id = qel.intent_id
JOIN chat_message cm ON cm.message_id = idet.message_id
JOIN sql_template st ON st.template_id = idet.template_id
ORDER BY qel.executed_at DESC;

COMMENT ON VIEW report_assistant_audit_trail IS 'NL assistant path replay for governance: message → intent → execution.';

COMMIT;

-- =======================================================================
-- Standalone illustrative queries (run ad hoc in pgAdmin / psql).
-- =======================================================================

/*

-- Q1: Patients with elevated composite risk awaiting any OPEN request at their site.

SELECT p.patient_id,
       p.full_name,
       p.risk_score,
       h.name AS hospital_name,
       r.request_id,
       r.request_type,
       r.urgency_level
FROM patient p
JOIN hospital h ON h.hospital_id = p.hospital_id
JOIN request r ON r.patient_id = p.patient_id
WHERE p.risk_score >= 85
  AND r.status ILIKE '%OPEN%'
ORDER BY p.risk_score DESC;

-- Q2: MTP-style narrative — lowest hemoglobin rows tied to blood demand rows.

SELECT p.full_name,
       mr.hemoglobin_level,
       br.units_required,
       br.blood_group_required,
       req.status
FROM medical_record mr
JOIN patient p ON p.patient_id = mr.patient_id
JOIN request req ON req.patient_id = p.patient_id AND req.request_type = 'BLOOD'
JOIN blood_request_details br ON br.request_id = req.request_id
WHERE mr.hemoglobin_level IS NOT NULL
  AND mr.hemoglobin_level < 10
ORDER BY mr.hemoglobin_level ASC
LIMIT 25;

-- Q3: Deferred / unavailable donor roster (supply planning).

SELECT donor_id,
       full_name,
       donor_type,
       availability_status,
       eligibility_status
FROM donor
WHERE eligibility_status ILIKE '%defer%'
   OR availability_status ILIKE '%unavail%';

-- Q4: Transplants in the last sliding 90 calendar days from CURRENT_DATE.

SELECT t.*
FROM transplant t
WHERE t.transplant_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY t.transplant_date DESC;

-- Q5: Cross-tab style — INTENT codes executed successfully.

SELECT st.intent_code,
       COUNT(*) AS runs,
       AVG(q.rows_returned)::NUMERIC(10,2) AS avg_rows
FROM query_execution_log q
JOIN intent_detection i ON i.intent_id = q.intent_id
JOIN sql_template st ON st.template_id = i.template_id
WHERE q.execution_status = 'SUCCESS'
GROUP BY st.intent_code
ORDER BY runs DESC;

*/
