# HackerRank Orchestrate (Oct 2026) - "Ghost Data Still Exists" Submission Instructions

This document records the exact specifications, hard constraints, working methodology, deliverable requirements, and evaluation guidelines for the "Ghost Data Still Exists" challenge.

---

## 0. Confirmed Fixed Specifications (from AGENTS.md & Sample Verification)
1. **Remediation Order Precedence**: Disable active data flows and block unsafe restores BEFORE changing dependent records, and process downstream copies before their source records.
2. **Strict Cutoff (`audit_at`)**: Use only information available at or before each case’s `audit_at`. Never cite or consider evidence captured after `audit_at`.
3. **Evidence ID Conventions**:
   - `evidence_id` is `""` (empty string) for proposed remediation and future verification steps in `INCOMPLETE` cases.
   - Findings and `COMPLETE` verification checks MUST cite a real participant-visible `file_id`, `activity_id`, or `audit_id`.
4. **Replication Drift Detection**: SQL evidence can include replicas (primary, regional, reporting, failover); compare tables and snapshot times for replication drift.
5. **Multilingual Intent & `NOT_APPLICABLE`**: `request_text` can be in different languages (English, French, Portuguese, Spanish, Japanese, Korean) and must actually authorize deletion. Access, correction, export, login assist, and marketing opt-out requests are `NOT_APPLICABLE` with `steps_json = []`.
6. **Output & Entry Point**:
   - `output.csv` must be generated at the repository root with exactly 518 data rows sorted by `case_id`.
   - `code/main.py` is the runnable entry point.

---

## 1. Goal
Build a runnable deletion-audit agent that reads `dataset/` and writes `output.csv` with exactly one row per case in `deletion_requests.csv` (518 rows, sorted by `case_id`).
- **Schema**: `case_id,deletion_status,steps_json`

---

## 2. Mandatory Rules & Guidelines
- Read `problem_statement.md`, `README.md`, and any `AGENTS.md` or instruction files in the repo FIRST upon provision.
- Follow every rule in them, including:
  - Chat-transcript logging (`log.txt`)
  - Code directory layout (`code/`)
- **Hard Constraints**:
  - **No hardcoded case IDs, emails, labels, or file-specific answers.** All logic must be general and rule-driven from `deletion_rules.csv`.
  - Must read the provided CSVs and the evidence files in `dataset/evidence/` (PDF, images, logs, JSON, SQLite-compatible SQL snapshots).
  - Must include an evaluation workflow and the deliverables listed below.
  - **No API keys in code.** Read them from environment variables and provide `.env.example`.

---

## 3. Working Method (Strict Order - Report findings before moving on)

### Step 1: EXPLORE (Completed)
- Inspect every file in `dataset/`.
- Report:
  - Columns
  - Row counts
  - Distinct values of categorical fields
  - Evidence file types
  - Mapping mechanism of `evidence_files.csv` to actual files
- Read 10 to 15 diverse sample cases end to end.

### Step 2: REVERSE-ENGINEER THE SPEC
- Trace `sample_deletion_requests.csv` plus `sample_output.csv`.
- For each sample case, trace why each output step exists:
  - Which identifier, record, `system_activity` row, or evidence file produced it.
- Document the derived rules into `docs/RULES.md`, including:
  1. How current and historical identifiers (`user_identities`, `user_audit_log`: email changes, email hash, phone, name) are resolved, and how chained/renamed emails are handled.
  2. How `NOT_APPLICABLE` is detected (`request_text` that is not a deletion request, or represents a different intent).
  3. How state at `audit_at` is determined (ignore activity after `audit_at`; `reported_status` is only a claim).
  4. How each data category in `deletion_rules.csv` maps to `DELETE` / `REDACT` / `ANONYMIZE` / `RETAIN`, including the tombstone rule (`user_id` may stay, but `name`, `email`, `phone`, and `email_hash` must be removed).
  5. Which `system_activity` entries count as active data flows (`sync`, `import`, `export`) or restore risks (`backup`, `restore`) at `audit_at`, and when a flow is disabled or superseded.
  6. How a sync job can re-create data after a delete.

### Step 3: DESIGN HYBRID PIPELINE
- **Deterministic Core**:
  - CSV parsing
  - Identity resolution
  - SQL snapshot querying (load with `sqlite3`)
  - JSON and log parsing
  - Time-based state reconstruction
  - Rule application
  - Step ordering
  - JSON serialization & schema validation
- **LLM/VLM Only Where Needed**:
  - Unstructured evidence (PDFs, images, free-text logs, ambiguous `request_text`)
  - Structured JSON output with strict schemas
  - Cache every call on a content hash
  - Batch where possible
  - Use the cheapest model that works
  - Record per-call input and output tokens
- **Core Principle**: Everything extracted by LLM must pass through the deterministic rule engine. The LLM extracts facts; code makes the decisions.

### Step 4: IMPLEMENTATION
- Directory layout: `code/` (Python preferred).
- Modules:
  - `loaders/`
  - `identity_resolver/`
  - `evidence_extractors/` (sql, json, log, pdf, image)
  - `state_reconstructor/`
  - `rule_engine/`
  - `plan_builder/`
  - `validator/`
  - CLI: `python code/main.py --input dataset/deletion_requests.csv --output output.csv`

### Step 5: OUTPUT RULES & VALIDATOR ENFORCEMENT
Must enforce in a validator that fails loudly:
- **Phases ordered**: `FINDING`, `REMEDIATION`, `VERIFICATION`.
- `step_no` starts at 1 and increments sequentially by 1.
- Within each phase, order by the operation order in the Allowed Operations table, then `system_id` ascending, then `resource_id` ascending.
- Allowed `(phase, operation, state)` triples only, exactly as in the specification table.
- **COMPLETE**: verification steps only, each citing a real `file_id`, `activity_id`, or `audit_id`.
- **INCOMPLETE**: findings (with `evidence_id`), the full remediation plan, and verification steps; remediation and verification `evidence_id` is an empty string `""`.
- **NOT_APPLICABLE**: `steps_json` is `[]`.
- Retained records get `VERIFY_RECORD_PRESENT`.
- Tombstones get `REDACT` then `VERIFY_RECORD_REDACTED`.
- Every active flow gets `REPORT_ACTIVE_DATA_FLOW`, `DISABLE_DATA_FLOW`, then `VERIFY_DATA_FLOW_DISABLED`.
- Every restore risk gets `REPORT_RESTORE_RISK`, `BLOCK_RESTORE`, then `VERIFY_RESTORE_BLOCKED`.
- Disable flows and block restores BEFORE deleting data.
- Downstream copies processed BEFORE their source records.
- Exactly 518 rows, sorted by `case_id`, valid CSV quoting for the JSON column.

### Step 6: EVALUATION WORKFLOW
- Build `code/evaluation/main.py` that scores against `sample_output.csv`:
  - Case-level status accuracy and confusion matrix
  - Step-level precision, recall, and F1 on `(phase, operation, system_id, resource_id, state, evidence_id)`
  - Field-level accuracy per field
  - Sequence accuracy (exact order match, plus longest common subsequence ratio)
- Create at least 3 additional evaluation cases in `code/evaluation/extra_cases/` (e.g. email changed twice, tombstone with leaked phone, sync job re-creating a deleted record, restore-risk backup, non-deletion request) with hand-written expected outputs.
- Iterate: diagnose root cause (identity, state, rule, ordering, evidence citation), fix generally (never special-case a sample), and re-run.

### Step 7: DELIVERABLES
1. `code/` with:
   - `README.md` (setup, run, architecture, design decisions)
   - `prompts/` (all prompts used)
   - Config files
2. `code/evaluation/evaluation_report.md` with:
   - All required metrics
   - Extra cases analysis
   - "Failures found and improvements made" section
3. `code/evaluation/usage_report.md` for final full-dataset run:
   - Providers and models
   - Number of calls
   - Input and output tokens (totals & per-request averages)
   - Estimated total and per-request cost
   - Per-model plus overall totals if multiple models
4. `output.csv` for all 518 requests at the repository root.
5. Submission archive excluding `venv/`, `node_modules/`, build artifacts, `dataset/`, and `data/`.

---

## 4. Quality Bar
- Idempotent, deterministic runs (`temperature: 0`, cached LLM results).
- Unit tests for identity resolver, state reconstruction, ordering, and validator.
- Log warnings for any case with low confidence or unparseable evidence; compile a summary list of those cases.
- Progress updates: short summary after each phase (findings, decisions, rationale, next steps).
