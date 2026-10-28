# 👻 Ghost Data Still Exists: Autonomous AI Deletion-Audit Agent
### HackerRank Orchestrate (October 2026) Hackathon Submission

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Benchmark Accuracy](https://img.shields.io/badge/Benchmark%20Accuracy-100%25-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Status-Completed%20%26%20Submitted-success.svg)]()

---

## 📖 Table of Contents
1. [Executive Summary & Problem Statement](#-executive-summary--problem-statement)
2. [My Hackathon Journey & Strategy](#-my-hackathon-journey--strategy)
3. [Architecture & Pipeline Design](#-architecture--pipeline-design)
4. [Key Engineering Innovations](#-key-engineering-innovations)
5. [Evaluation Results & Benchmark Performance](#-evaluation-results--benchmark-performance)
6. [Participant-Created Custom Edge Cases](#-participant-created-custom-edge-cases)
7. [Repository Structure](#-repository-structure)
8. [Setup, Installation & Usage](#-setup-installation--usage)
9. [AI Interview Defense & Takeaways](#-ai-interview-defense--takeaways)

---

## 🌟 Executive Summary & Problem Statement

In October 2026, I participated in the **HackerRank Orchestrate** hackathon challenge: **Ghost Data Still Exists**.

### The Real-World Scenario
Northstar Shop (an imaginary e-commerce platform) suffered a **\$2.4 million loss** after a customer who had requested complete deletion returned weeks later as a "ghost" in internal systems. Every platform dashboard reported the deletion as **"Complete."** Yet, when the customer attempted to re-register, the service failed with: *“This email is already registered.”*

An internal forensic investigation revealed a catastrophic compliance failure: personal data lingered in secondary databases, failover replicas, search indexes, analytics dumps, customer support attachments, and unstructured server logs. Worse still, an active background synchronization pipeline had re-ingested data that the primary database had deleted.

### The Objective
To build an autonomous, evidence-driven AI deletion-audit agent that:
- Audits **518 evaluation requests** (`dataset/deletion_requests.csv`).
- Accurately classifies each case as `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE` (non-deletion requests).
- Evaluates empirical ground truth at the exact cutoff timestamp `audit_at`, overriding misleading workflow claims.
- Discovers ghost records, active sync flows, and restore risks.
- Formulates a strictly ordered, policy-compliant remediation plan (`FINDING` $\to$ `REMEDIATION` $\to$ `VERIFICATION`).
- Preserves legal tombstones (retaining stable `user_id` while removing all direct PII).

---

## 🚀 My Hackathon Journey & Strategy

I approached this hackathon with a rigorous, engineering-first methodology divided into six distinct milestones:

```
┌─────────────────┐     ┌───────────────────────┐     ┌─────────────────────┐
│ 1. Deep Data    │ ──> │ 2. Reverse-Engineered │ ──> │ 3. Hybrid Pipeline  │
│    Forensics    │     │    Deletion Rules     │     │    Architecture     │
└─────────────────┘     └───────────────────────┘     └─────────────────────┘
         │                                                       │
         ▼                                                       ▼
┌─────────────────┐     ┌───────────────────────┐     ┌─────────────────────┐
│ 6. AI Interview │ <── │ 5. Edge-Case Creation │ <── │ 4. 100% Benchmark   │
│    Defense      │     │    & Verification     │     │    Evaluation       │
└─────────────────┘     └───────────────────────┘     └─────────────────────┘
```

### Milestone 1: Deep Data Forensics & Cataloging
- Parsed and indexed all **94 evidence files** (`dataset/evidence/`) spanning 24 SQL database snapshots, 28 JSON bundles, 26 structured server logs, 4 PDF documents, 11 screenshot images, and plaintext handover records.
- Built an in-memory inverted catalog of **2,915 evidence entities** keyed on subject hashes, historical emails, phone numbers, and distributed trace IDs in under 3.5 seconds.

### Milestone 2: Reverse-Engineering Policies & Lifecycle Rules
- Analyzed `dataset/sample_deletion_requests.csv` against `dataset/sample_output.csv` to derive hidden operational dynamics:
  - **Evidence Precedence**: Operational logs and reported workflow statuses are merely *claims*. An empirical SQL snapshot showing 0 rows overrides a "PARTIAL" activity result (e.g. `case_02`).
  - **Support Record Taxonomy**: Distinguished between `SUPPORT_MESSAGE` (Rule 05: Redaction) and `SUPPORT_ATTACHMENT` (Rule 06: Deletion).
  - **Replication Drift**: Detected database replicas (`evidence_61` / `support_replica.log`) missing deletion markers (`marker_found=false, rows=1`).
  - **Account Tombstones (Rule 01)**: The internal `user_id` may stay, but name, email, phone, and email hash must be redacted—never fully deleted.
- Documented these derived rules into [`docs/RULES.md`](./docs/RULES.md).

### Milestone 3: Hybrid Pipeline Architecture
- Designed a **deterministic-first core** in Python. While many participants relied entirely on unconstrained LLM calls (resulting in hallucinations, high costs, and non-deterministic ordering), my solution executes all data parsing, multi-hop identity resolution, temporal state reconciliation, and rule sequencing through deterministic code.
- Multimodal and LLM capabilities are strictly isolated for unstructured text extraction and visual artifacts, ensuring 100% predictable, reproducible outputs at minimal token cost.

### Milestone 4: Implementation & 100% Benchmark Verification
- Implemented modular code in `code/` with strict separation of concerns.
- Verified against the 32 ground-truth sample requests, reaching **100.00% status accuracy, 100.00% step precision/recall/F1, and 100.00% sequence accuracy**.

### Milestone 5: Stress-Testing with Handcrafted Edge Cases
- Created four custom, complex test cases in `code/evaluation/extra_cases/` to test chained email renames, cleartext phone leaks in tombstones, ghost data sync loops, and German GDPR DSAR access requests.

### Milestone 6: Final Packaging & AI Interview Defense
- Executed full audit across all 518 evaluation requests, generating [`output.csv`](./output.csv) with zero validator errors.
- Authored [`code/evaluation/evaluation_report.md`](./code/evaluation/evaluation_report.md) and [`code/evaluation/usage_report.md`](./code/evaluation/usage_report.md).
- Packaged [`code.zip`](./code.zip) and [`agent-trace.zip`](./agent-trace.zip) according to contest standards.

---

## 🏗️ Architecture & Pipeline Design

```
                     ┌──────────────────────────────┐
                     │   deletion_requests.csv      │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │ 1. Intent Classifier         │ ──[ Non-Deletion ]──> NOT_APPLICABLE (steps: [])
                     │    (Multilingual Stemming)   │
                     └──────────────┬───────────────┘
                                    │ [ Deletion Authorized ]
                                    ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│  user_identities.csv    │  │ 2. Identity Resolver         │
│  user_audit_log.csv     │──>   (Multi-hop Alias Chaining) │
└─────────────────────────┘  └──────────────┬───────────────┘
                                            │
                                            ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│  Evidence Catalog       │──> 3. State Reconstructor       │ <── Cutoff at audit_at
│  (SQL, JSON, Logs, PDF) │  │    (Claims vs. Evidence)     │
└─────────────────────────┘  └──────────────┬───────────────┘
                                            │
                                            ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│  deletion_rules.csv     │──> 4. Plan Builder & Orderer    │
│  (Tombstones, Policies) │  │    (FIND -> REM -> VERIFY)   │
└─────────────────────────┘  └──────────────┬───────────────┘
                                            │
                                            ▼
                             ┌──────────────────────────────┐
                             │ 5. Output Validator & Serializer│
                             └──────────────┬───────────────┘
                                            │
                                            ▼
                                       output.csv
```

### Module Responsibilities:
- **`code/rule_engine/intent_classifier.py`**: Multi-lingual stemming lexicon detecting whether `request_text` actually authorizes deletion (isolating non-deletion DSAR/access/correction requests).
- **`code/identity_resolver/resolver.py`**: Resolves `user_id`, historical emails across rename chains, phone numbers, and email SHA-256 hashes.
- **`code/evidence_extractors/`**: SQLite query engine for `.sql` database snapshots, JSON parsers, trace-correlated log parsers, PDF extractors, and OCR screenshot mappers.
- **`code/state_reconstructor/reconstructor.py`**: Evaluates true entity state at cutoff timestamp `audit_at`.
- **`code/plan_builder/builder.py`**: Formulates canonical plans conforming to the contractual Allowed Operations table and priority rules.
- **`code/validator/output_validator.py`**: Enforces strict schema, phase sequence, operation states, consecutive numbering, and citation validity.

---

## 💡 Key Engineering Innovations

### 1. Evidence Precedence Over Operational Claims
Deletion workers in `system_activity.csv` often report `SUCCESS` or `PARTIAL` based only on local service calls. Our agent cross-examines claims against empirical database snapshots and replica logs captured on or before `audit_at`. If a snapshot shows 0 rows, the resource is confirmed `ABSENT`. Conversely, if replica logs show missing deletion markers (`evidence_61`), a finding is raised regardless of what the workflow reported.

### 2. Multi-Hop Distributed Trace Log Correlation
In server logs (`structured_service_events_*.log`), user identifiers (e.g. `email` or `user_id`) appear on line $N$, while resource identifiers (e.g. `search_XXXX`, `analytics_XXXX`) appear on line $N+k$. Our `LogEvidenceExtractor` aggregates events by `trace_id` and `requestId`, linking resources that naive line-by-line parsers miss entirely.

### 3. Safe Dependency-Aware Remediation Sequencing
When remediating ghost data, ordering is paramount:
1. **Disable Active Data Flows** (`DISABLE_DATA_FLOW`) to prevent active pipelines from repopulating records mid-operation.
2. **Block Unsafe Restores** (`BLOCK_RESTORE`) to prevent automated backups from re-injecting deleted data.
3. **Remediate Dependent & Downstream Records** before modifying primary records.
4. **Redact Tombstones** (`REDACT_RECORD`) to preserve internal IDs without exposing PII.

---

## 📊 Evaluation Results & Benchmark Performance

The pipeline was validated against the 32 ground-truth sample requests in `dataset/sample_output.csv`:

| Evaluation Metric | Achieved Score | Benchmark Target | Verdict |
|---|---|---|---|
| **Case-Level Status Accuracy** | **100.00%** (32 / 32) | $\ge 90.00\%$ | **PERFECT** |
| **Step Precision** | **100.00%** (127 / 127) | $\ge 90.00\%$ | **PERFECT** |
| **Step Recall** | **100.00%** (127 / 127) | $\ge 90.00\%$ | **PERFECT** |
| **Step F1-Score** | **100.00%** | $\ge 90.00\%$ | **PERFECT** |
| **Exact Sequence Accuracy** | **100.00%** (32 / 32) | $\ge 85.00\%$ | **PERFECT** |
| **Average LCS Ratio** | **100.00%** | $\ge 90.00\%$ | **PERFECT** |
| **Field Accuracy (`step_no`, `phase`, `operation`, `system_id`, `resource_id`, `state`, `evidence_id`)** | **100.00%** (127 / 127) | $100.00\%$ | **PERFECT** |

### Confusion Matrix
| Ground Truth \ Predicted | COMPLETE | INCOMPLETE | NOT_APPLICABLE |
|---|---|---|---|
| **COMPLETE** | **10** | 0 | 0 |
| **INCOMPLETE** | 0 | **22** | 0 |
| **NOT_APPLICABLE** | 0 | 0 | 0 |

### Resource & Financial Cost Efficiency
- **Total Requests Audited**: 518 cases
- **Execution Time**: ~4.2 seconds for full 518-case audit
- **Total Tokens Consumed**: 315,980 tokens
- **Total Estimated Cost**: **\$0.059 USD** (~$0.000114 per request)

---

## 🧪 Participant-Created Custom Edge Cases

To thoroughly stress-test the pipeline beyond the provided public samples, I authored 4 specialized edge-case scenarios in [`code/evaluation/extra_cases/`](./code/evaluation/extra_cases/):

1. **`extra_01` — Chained Email Renames with Replica Leakage (`INCOMPLETE`)**:  
   User changed emails: `elena.v@oldmail.com` $\to$ `elena.rostova@work.com` $\to$ `elena.rostova@fastmail.com`. Primary DB was deleted, but support replica (`evidence_61`) retained historical PII.  
   *Verified: Raised `REPORT_EXPOSED_PII` citing `evidence_61` and planned `REDACT_RECORD`.*

2. **`extra_02` — Account Tombstone Leaking Cleartext Phone (`INCOMPLETE`)**:  
   Account tombstone retained `user_id` as allowed, but database snapshot `evidence_54` revealed phone number was accidentally left intact.  
   *Verified: Detected PII leak, mandated `REDACT_RECORD`, prevented illegal full deletion.*

3. **`extra_03` — Active Synchronization Connector Recreation Loop (`INCOMPLETE`)**:  
   Search record was deleted, but active connector `data_flow_9927` in `integration_service` remained scheduled to repopulate data from cache.  
   *Verified: Formulated `DISABLE_DATA_FLOW` before touching dependent search records.*

4. **`extra_04` — Multilingual Non-Deletion Request (`NOT_APPLICABLE`)**:  
   German GDPR Article 15 Data Subject Access Request (*"Ich bitte um eine vollständige Kopie aller meiner gespeicherten Daten..."*).  
   *Verified: Classified as `NOT_APPLICABLE` with `steps_json = []`.*

---

## 📁 Repository Structure

```text
├── README.md                      # Comprehensive project overview & hackathon journey
├── requirements.txt               # Lightweight Python dependencies
├── .env.example                   # Environment variable template
├── problem_statement.md           # Official challenge contract
├── MASTER_PROMPT.md               # Master technical guidelines and constraints
├── AGENTS.md                      # AI agent logging & challenge protocol
├── log.txt                        # Complete audit chat transcript
├── output.csv                     # Final 518-case prediction submission
├── code.zip                       # Official solution package
├── agent-trace.zip                # Official agent trace package
├── docs/
│   └── RULES.md                   # Reverse-engineered deletion policies & state logic
├── evaluation/
│   ├── evaluation_report.md       # Benchmark metrics, confusion matrix, & extra cases
│   └── usage_report.md            # Token accounting and cost breakdown
├── dataset/                       # Participant-facing evaluation inputs & evidence
└── code/
    ├── main.py                    # CLI entry point and pipeline orchestrator
    ├── config.py                  # Path and configuration constants
    ├── loaders/                   # CSV dataset loaders
    ├── identity_resolver/         # Multi-hop identity chaining resolver
    ├── evidence_extractors/       # SQL, JSON, log, PDF, and image extractors
    ├── rule_engine/               # Multilingual intent classifier & policy rules
    ├── state_reconstructor/       # Temporal state reconciliation at audit_at
    ├── plan_builder/              # Ordered lifecycle plan builder
    ├── validator/                 # Strict schema & ordering validator
    └── evaluation/                # Benchmark scoring engine & extra test cases
```

---

## 🛠️ Setup, Installation & Usage

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/awneesh-mishra/ghost-data-audit-agent.git
cd ghost-data-audit-agent

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Full Deletion Audit Pipeline
To process all 518 evaluation requests and write the validated `output.csv`:
```bash
python code/main.py --input dataset/deletion_requests.csv --output output.csv
```

### 3. Run the Evaluation Suite
To execute automated scoring against ground truth:
```bash
python code/evaluation/main.py
```

---

## 🎙️ AI Interview Defense & Takeaways

During the post-submission AI Interview, I successfully defended the design against rigorous technical inquiries:

1. **Deterministic vs. LLM Trade-off**: Explained why a deterministic core with targeted fact extraction outperforms purely generative agents in regulatory compliance, eliminating hallucinations while achieving 100% sequence accuracy.
2. **Empirical Ground Truth over Claims**: Highlighted real-world case failures where workflows report "Complete" prematurely, emphasizing why evidence snapshots captured at or before `audit_at` must supersede activity claims.
3. **Recreation Risk Mitigation**: Defended the necessity of ordering flow disabling and restore blocking prior to record modification to permanently prevent ghost data resurrection.

---

## 👤 Author & Acknowledgments

- **Participant**: Awneesh Mishra ([awneeshmishra433@gmail.com](mailto:awneeshmishra433@gmail.com))
- **Event**: HackerRank Orchestrate (October 2026)
- **Challenge**: [Ghost Data Still Exists](https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists)
