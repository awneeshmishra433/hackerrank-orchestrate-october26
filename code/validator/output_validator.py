import csv
import json
from typing import List, Dict, Any, Tuple

class OutputValidator:
    """
    Validates submission output against challenge constraints and schemas.
    """

    ALLOWED_TRIPLES = {
        ('FINDING', 'REPORT_REMAINING_RECORD', 'PRESENT'),
        ('FINDING', 'REPORT_EXPOSED_PII', 'PRESENT'),
        ('FINDING', 'REPORT_ACTIVE_DATA_FLOW', 'ACTIVE'),
        ('FINDING', 'REPORT_RESTORE_RISK', 'ACTIVE'),
        ('REMEDIATION', 'DISABLE_DATA_FLOW', 'DISABLED'),
        ('REMEDIATION', 'BLOCK_RESTORE', 'BLOCKED'),
        ('REMEDIATION', 'DELETE_RECORD', 'ABSENT'),
        ('REMEDIATION', 'REDACT_RECORD', 'REDACTED'),
        ('REMEDIATION', 'ANONYMIZE_RECORD', 'ANONYMIZED'),
        ('VERIFICATION', 'VERIFY_RECORD_ABSENT', 'ABSENT'),
        ('VERIFICATION', 'VERIFY_RECORD_PRESENT', 'PRESENT'),
        ('VERIFICATION', 'VERIFY_RECORD_REDACTED', 'REDACTED'),
        ('VERIFICATION', 'VERIFY_RECORD_ANONYMIZED', 'ANONYMIZED'),
        ('VERIFICATION', 'VERIFY_DATA_FLOW_DISABLED', 'DISABLED'),
        ('VERIFICATION', 'VERIFY_RESTORE_BLOCKED', 'BLOCKED'),
    }

    FINDING_ORDER = ['REPORT_REMAINING_RECORD', 'REPORT_EXPOSED_PII', 'REPORT_ACTIVE_DATA_FLOW', 'REPORT_RESTORE_RISK']
    REMEDIATION_ORDER = ['DISABLE_DATA_FLOW', 'BLOCK_RESTORE', 'DELETE_RECORD', 'REDACT_RECORD', 'ANONYMIZE_RECORD']
    VERIFICATION_ORDER = ['VERIFY_RECORD_ABSENT', 'VERIFY_RECORD_PRESENT', 'VERIFY_RECORD_REDACTED', 'VERIFY_RECORD_ANONYMIZED', 'VERIFY_DATA_FLOW_DISABLED', 'VERIFY_RESTORE_BLOCKED']

    @classmethod
    def validate_file(cls, file_path: str, expected_cases: int = 518) -> Tuple[bool, List[str]]:
        errors = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header != ['case_id', 'deletion_status', 'steps_json']:
                    errors.append(f"Invalid header: {header}. Expected ['case_id', 'deletion_status', 'steps_json']")

                rows = list(reader)
        except Exception as e:
            return False, [f"Failed to read CSV: {e}"]

        if len(rows) != expected_cases:
            errors.append(f"Expected {expected_cases} data rows, found {len(rows)}")

        prev_case_id = None
        for idx, row in enumerate(rows, 1):
            if len(row) != 3:
                errors.append(f"Row {idx} does not have exactly 3 columns: {row}")
                continue

            case_id, status, steps_str = row
            if prev_case_id and case_id <= prev_case_id:
                errors.append(f"Rows not sorted by case_id at row {idx}: {prev_case_id} then {case_id}")
            prev_case_id = case_id

            if status not in ['COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE']:
                errors.append(f"Row {idx} ({case_id}) has invalid status '{status}'")

            try:
                steps = json.loads(steps_str)
            except Exception as e:
                errors.append(f"Row {idx} ({case_id}) has invalid JSON: {e}")
                continue

            if not isinstance(steps, list):
                errors.append(f"Row {idx} ({case_id}) steps_json is not an array")
                continue

            if status == 'NOT_APPLICABLE' and steps != []:
                errors.append(f"Row {idx} ({case_id}) status is NOT_APPLICABLE but steps_json is not []")

            row_errors = cls.validate_steps(case_id, status, steps)
            errors.extend([f"Row {idx} ({case_id}): {err}" for err in row_errors])

        return (len(errors) == 0), errors

    @classmethod
    def validate_steps(cls, case_id: str, status: str, steps: List[Dict[str, Any]]) -> List[str]:
        errors = []
        if status == 'NOT_APPLICABLE':
            return errors

        phase_seen = 'NONE'
        prev_op_idx = -1
        prev_sys = ""
        prev_res = ""

        for i, s in enumerate(steps, 1):
            if s.get('step_no') != i:
                errors.append(f"Step {i} has step_no={s.get('step_no')}, expected {i}")

            phase = s.get('phase')
            op = s.get('operation')
            st = s.get('state')
            sys_id = s.get('system_id', '')
            res_id = s.get('resource_id', '')
            eid = s.get('evidence_id', '')

            # Check triple
            if (phase, op, st) not in cls.ALLOWED_TRIPLES:
                errors.append(f"Step {i} invalid triple: ({phase}, {op}, {st})")

            # Check phase order: FINDING -> REMEDIATION -> VERIFICATION
            if phase == 'FINDING':
                if phase_seen not in ['NONE', 'FINDING']:
                    errors.append(f"Step {i} FINDING out of order after {phase_seen}")
                phase_seen = 'FINDING'
                op_list = cls.FINDING_ORDER
            elif phase == 'REMEDIATION':
                if phase_seen not in ['NONE', 'FINDING', 'REMEDIATION']:
                    errors.append(f"Step {i} REMEDIATION out of order after {phase_seen}")
                phase_seen = 'REMEDIATION'
                op_list = cls.REMEDIATION_ORDER
            elif phase == 'VERIFICATION':
                phase_seen = 'VERIFICATION'
                op_list = cls.VERIFICATION_ORDER
            else:
                errors.append(f"Step {i} unknown phase '{phase}'")
                continue

            # Check operation order within phase
            cur_op_idx = op_list.index(op) if op in op_list else 99
            if phase != getattr(cls, '_last_phase', None):
                prev_op_idx = -1
                prev_sys = ""
                prev_res = ""
                cls._last_phase = phase

            if cur_op_idx < prev_op_idx:
                errors.append(f"Step {i} operation '{op}' ordered before previous operation in {phase}")
            elif cur_op_idx == prev_op_idx:
                if (sys_id, res_id) < (prev_sys, prev_res):
                    errors.append(f"Step {i} ({sys_id}, {res_id}) not sorted after ({prev_sys}, {prev_res})")

            prev_op_idx = cur_op_idx
            prev_sys = sys_id
            prev_res = res_id

            # Evidence id checks
            if status == 'COMPLETE':
                if phase != 'VERIFICATION':
                    errors.append(f"COMPLETE case has non-verification phase '{phase}' at step {i}")
                if not eid:
                    errors.append(f"COMPLETE case step {i} has empty evidence_id")
            elif status == 'INCOMPLETE':
                if phase in ['REMEDIATION', 'VERIFICATION'] and eid != "":
                    errors.append(f"INCOMPLETE case step {i} ({phase}) must have empty evidence_id, got '{eid}'")
                if phase == 'FINDING' and not eid:
                    errors.append(f"INCOMPLETE case step {i} (FINDING) has empty evidence_id")

        return errors

