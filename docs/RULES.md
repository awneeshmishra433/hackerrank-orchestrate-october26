# Specification and Derived Audit Rules: Ghost Data Still Exists

This document details the reverse-engineered rules, identity resolution mechanisms, state reconstruction algorithms, deletion policy mappings, and sequencing logic derived from `dataset/`, `AGENTS.md`, and the 32 ground-truth sample cases in `dataset/sample_output.csv`.

---

## 1. Identity Resolution & Identifier Chaining
A deletion request provides a single input email in `deletion_requests.csv`. This email may be current or historical.

### 1.1 Resolution Algorithm
1. **Primary Lookup**: Check `user_identities.csv` where `email` (case-insensitive) matches the request email.
   - If found, retrieve `user_id`, `name`, `phone`, `email_hash`, and current `email`.
2. **Historical / Audit Lookup**: If not found in `user_identities.csv`, search `user_audit_log.csv` where `field_name == 'email'` and `old_value` matches the request email.
   - Retrieve `user_id` from the matching audit log entry.
   - Look up the retrieved `user_id` in `user_identities.csv` to obtain the user's latest snapshot.
3. **Identifier Graph Construction**:
   - Collect all historical and current values across `user_identities.csv` and all `user_audit_log.csv` records for that `user_id`:
     - **Emails**: Current email + all `old_value` and `new_value` where `field_name == 'email'`.
     - **Phones**: Current phone + all historical phones where `field_name == 'phone'`.
     - **Email Hashes**: Current SHA-256 hash + all historical hashes where `field_name == 'email_hash'`.
     - **Names**: Current display/full name.
     - **User ID**: Stable identifier (e.g., `user_01`, `user_29`).
4. **Chained / Renamed Identifiers**:
   - Multi-hop renames (e.g. `email_v1 -> email_v2 -> email_v3`) are fully unified under the same `user_id` by traversing all audit events for that subject.

---

## 2. Intent Classification & `NOT_APPLICABLE` Detection
The `request_text` must explicitly authorize deletion of personal data or account closure.

### 2.1 Non-Deletion Intents
A request is classified as `NOT_APPLICABLE` (with `steps_json = []`) if the user expresses an intent other than deletion:
1. **Rectification / Data Correction**: Updating an out-of-date phone number, correcting misspelled names or profile fields.
2. **Access / Information Request**: Asking for a copy of held records, invoices, or personal data without requesting removal.
3. **Data Portability**: Requesting an export or download of personal information in a portable format while keeping the account active.
4. **Marketing Opt-Out**: Asking to stop promotional emails or unsubscribe from marketing lists while maintaining an active shopping account.
5. **Account Assistance**: Requesting password or login reset assistance.

### 2.2 Multilingual Handling
Requests may be written in English, French, Portuguese, Spanish, Japanese, or Korean. Standard deletion indicators in all languages (e.g. *delete*, *erase*, *close*, *supprimer*, *exclusão*, *eliminación*, *削除*, *삭제*) indicate deletion intent unless explicitly qualified by non-destructive terms (e.g. "leave the account active", "not asking for deletion", "keep the account as it is").

---

## 3. Time-Based State Reconstruction (`audit_at`)
1. **Temporal Cutoff**:
   - Any system activity, audit event, or evidence file with a timestamp strictly greater than the request's `audit_at` MUST BE COMPLETELY IGNORED.
   - Evidence created after `audit_at` must never be cited or used to decide the case.
2. **Claims vs Proof**:
   - `reported_status` in `deletion_requests.csv` and `reported_result` in `system_activity.csv` are merely claims.
   - The actual state of every resource at `audit_at` must be established from the latest available evidence and verified system activity up to `audit_at`.
3. **Replica & Failover Parity (Replication Drift)**:
   - When inspecting SQL snapshots, primary databases may report a record as absent, but secondary, regional, or failover replicas (e.g., `customer_accounts_failover_replica`) may still contain the record.
   - A record present in ANY active replica at `audit_at` is deemed `PRESENT`.

---

## 4. Policy Rules Mapping (`deletion_rules.csv`)

| Rule ID | Data Category | Target System | Condition | Required Action | Remediation Op | Expected Final State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rule_01` | USER_PROFILE | `account_service` | Always | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_02` | SECONDARY_IDENTIFIER | `account_service` | Always | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_03` | SEARCH_INDEX_ENTRY | `search_service` | Always | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_04` | CACHE_ENTRY | `cache_service` | Always | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_05` | SUPPORT_MESSAGE | `support_platform` | Conversation contains shared context | `REDACT` | `REDACT_RECORD` | `REDACTED` |
| `rule_06` | SUPPORT_ATTACHMENT | `support_platform` | Belongs only to deletion subject | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_07` | ANALYTICS_PROFILE | `analytics_platform` | Record attributable to user | `ANONYMIZE` | `ANONYMIZE_RECORD` | `ANONYMIZED` |
| `rule_08` | PRODUCT_TELEMETRY | `analytics_platform` | Record attributable to user | `ANONYMIZE` | `ANONYMIZE_RECORD` | `ANONYMIZED` |
| `rule_09` | USER_EXPORT | `export_service` | Always | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_10` | MARKETING_PROFILE | `marketing_platform` | Always | `DELETE` | `DELETE_RECORD` | `ABSENT` |
| `rule_11` | EMAIL_DELIVERY_LOG | `email_delivery_service` | Log contains user email | `REDACT` | `REDACT_RECORD` | `REDACTED` |
| `rule_12` | SECURITY_AUDIT_LOG | `security_service` | Within retention period | `RETAIN` | *(None - Retained)* | `PRESENT` |
| `rule_13` | LEGAL_HOLD_RECORD | `legal_retention_service`| Active legal hold | `RETAIN` | *(None - Retained)* | `PRESENT` |
| `rule_14` | BACKUP_ARCHIVE | `backup_service` | Restore access can be blocked | `RETAIN` / `BLOCK` | `BLOCK_RESTORE` | `BLOCKED` |
| `rule_15` | ACCOUNT_TOMBSTONE | `identity_service` | Preserves stable user_id | `REDACT` | `REDACT_RECORD` | `REDACTED` |

### 4.1 Tombstone Rule
For `identity_service` tombstones (e.g. `tombstone_17`, `tombstone_440`, `tombstone_9178`):
- The internal `user_id` may remain to maintain foreign-key integrity for retained records (`security_service` audit logs, legal holds).
- All direct personal identifiers (`name`, `email`, `phone`, `email_hash`) MUST be redacted.
- If direct identifiers remain exposed at `audit_at`, report `REPORT_EXPOSED_PII` (State: `PRESENT`), remediate with `REDACT_RECORD` (State: `REDACTED`), and verify with `VERIFY_RECORD_REDACTED` (State: `REDACTED`).

---

## 5. Active Data Flows & Restore Risks

### 5.1 Active Data Flows (`integration_service`)
- Connectors that sync data downstream (e.g. `analytics_identity_bridge`, `customer_events_connector`, `support_profile_sync`) that remain `enabled == True` at `audit_at` can copy or recreate personal data.
- **Finding**: `REPORT_ACTIVE_DATA_FLOW` (State: `ACTIVE`).
- **Remediation**: `DISABLE_DATA_FLOW` (State: `DISABLED`).
- **Verification**: `VERIFY_DATA_FLOW_DISABLED` (State: `DISABLED`).
- **Superseding**: If a `DISABLE_DATA_FLOW` event with `SUCCESS` occurred on or before `audit_at`, the flow is `DISABLED`.

### 5.2 Restore Risks (`backup_service`)
- Backup archives where restore access remains allowed (`restore_allowed == True`) at `audit_at` pose a risk of repopulating deleted records.
- **Finding**: `REPORT_RESTORE_RISK` (State: `ACTIVE`).
- **Remediation**: `BLOCK_RESTORE` (State: `BLOCKED`).
- **Verification**: `VERIFY_RESTORE_BLOCKED` (State: `BLOCKED`).
- **Superseding**: If a `BLOCK_RESTORE` event with `SUCCESS` occurred on or before `audit_at`, restore access is `BLOCKED`.

### 5.3 Recreation by Sync Jobs
- If a record was deleted (`DELETE_RECORD | SUCCESS`), but subsequent system activity shows a `SYNC_RECORD | SUCCESS` or replication event before `audit_at`, the record has been recreated as ghost data.
- It must be reported as `REPORT_REMAINING_RECORD` (State: `PRESENT`).

---

## 6. Ordering & Plan Generation Rules

### 6.1 Phase Order
All plans strictly follow the three-phase pipeline:
1. `FINDING`
2. `REMEDIATION`
3. `VERIFICATION`

### 6.2 Operation Precedence (within each Phase)
Within each phase, operations must appear in the exact order defined by the Allowed Operations specification:

#### Phase 1: FINDING
1. `REPORT_REMAINING_RECORD`
2. `REPORT_EXPOSED_PII`
3. `REPORT_ACTIVE_DATA_FLOW`
4. `REPORT_RESTORE_RISK`

#### Phase 2: REMEDIATION
1. `DISABLE_DATA_FLOW` (disable processes before modifying data)
2. `BLOCK_RESTORE` (block restores before modifying data)
3. `DELETE_RECORD` (downstream copies processed before source records)
4. `REDACT_RECORD`
5. `ANONYMIZE_RECORD`

#### Phase 3: VERIFICATION
1. `VERIFY_RECORD_ABSENT`
2. `VERIFY_RECORD_PRESENT`
3. `VERIFY_RECORD_REDACTED`
4. `VERIFY_RECORD_ANONYMIZED`
5. `VERIFY_DATA_FLOW_DISABLED`
6. `VERIFY_RESTORE_BLOCKED`

### 6.3 Tie-Breaking Sort
Within the same operation, sort steps by:
1. `system_id` ascending (alphabetical)
2. `resource_id` ascending (alphabetical)

### 6.4 `evidence_id` Citation Rules
- In a `COMPLETE` case: verification steps cite the real `file_id`, `activity_id`, or `audit_id` that proves the compliant state.
- In an `INCOMPLETE` case:
  - Findings cite the real `file_id`, `activity_id`, or `audit_id` that discovered the violation.
  - Proposed remediation steps cite `""` (empty string).
  - Future verification steps cite `""` (empty string).
- In a `NOT_APPLICABLE` case: `steps_json = []`.

