from typing import List, Dict, Any, Tuple
from code.state_reconstructor.reconstructor import ResourceState

class PlanBuilder:
    """
    Builds the ordered plan of findings, remediation actions, and verification checks.
    """

    FINDING_ORDER = {
        'REPORT_REMAINING_RECORD': 1,
        'REPORT_EXPOSED_PII': 2,
        'REPORT_ACTIVE_DATA_FLOW': 3,
        'REPORT_RESTORE_RISK': 4
    }

    REMEDIATION_ORDER = {
        'DISABLE_DATA_FLOW': 1,
        'BLOCK_RESTORE': 2,
        'DELETE_RECORD': 3,
        'REDACT_RECORD': 4,
        'ANONYMIZE_RECORD': 5
    }

    VERIFICATION_ORDER = {
        'VERIFY_RECORD_ABSENT': 1,
        'VERIFY_RECORD_PRESENT': 2,
        'VERIFY_RECORD_REDACTED': 3,
        'VERIFY_RECORD_ANONYMIZED': 4,
        'VERIFY_DATA_FLOW_DISABLED': 5,
        'VERIFY_RESTORE_BLOCKED': 6
    }

    @classmethod
    def build_plan(
        cls,
        is_deletion_auth: bool,
        resources: Dict[str, ResourceState],
        default_evidence_id: str = ""
    ) -> Tuple[str, List[Dict[str, Any]]]:

        if not is_deletion_auth:
            return 'NOT_APPLICABLE', []

        findings = []
        remediations = []
        verifications = []

        # Check compliance across all resources
        is_complete = True
        for res in resources.values():
            if not res.is_compliant:
                is_complete = False
                break

        # If complete, only verification steps citing real evidence
        if is_complete:
            for rid, res in resources.items():
                v_op, v_state = cls._get_verification_for_resource(res)
                eid = res.evidence_id or default_evidence_id
                verifications.append({
                    'phase': 'VERIFICATION',
                    'system_id': res.system_id,
                    'resource_id': rid,
                    'operation': v_op,
                    'state': v_state,
                    'evidence_id': eid
                })

            # Sort verifications
            verifications.sort(key=lambda s: (cls.VERIFICATION_ORDER.get(s['operation'], 99), s['system_id'], s['resource_id']))
            for idx, s in enumerate(verifications, 1):
                s['step_no'] = idx

            return 'COMPLETE', verifications

        # Incomplete case: Findings + Remediation + Post-remediation Verification
        for rid, res in resources.items():
            if not res.is_compliant:
                # Add Finding
                f_op, f_state = cls._get_finding_for_resource(res)
                eid = res.evidence_id or default_evidence_id
                findings.append({
                    'phase': 'FINDING',
                    'system_id': res.system_id,
                    'resource_id': rid,
                    'operation': f_op,
                    'state': f_state,
                    'evidence_id': eid
                })

                # Add Remediation
                r_op, r_state = cls._get_remediation_for_resource(res)
                remediations.append({
                    'phase': 'REMEDIATION',
                    'system_id': res.system_id,
                    'resource_id': rid,
                    'operation': r_op,
                    'state': r_state,
                    'evidence_id': ""
                })

            # Post-remediation verification covers all resources
            v_op, v_state = cls._get_verification_for_resource(res)
            verifications.append({
                'phase': 'VERIFICATION',
                'system_id': res.system_id,
                'resource_id': rid,
                'operation': v_op,
                'state': v_state,
                'evidence_id': ""
            })

        # Sort within each phase
        findings.sort(key=lambda s: (cls.FINDING_ORDER.get(s['operation'], 99), s['system_id'], s['resource_id']))
        remediations.sort(key=lambda s: (cls.REMEDIATION_ORDER.get(s['operation'], 99), s['system_id'], s['resource_id']))
        verifications.sort(key=lambda s: (cls.VERIFICATION_ORDER.get(s['operation'], 99), s['system_id'], s['resource_id']))

        all_steps = findings + remediations + verifications
        for idx, s in enumerate(all_steps, 1):
            s['step_no'] = idx

        return 'INCOMPLETE', all_steps

    @staticmethod
    def _get_finding_for_resource(res: ResourceState) -> Tuple[str, str]:
        if res.is_active_flow:
            return 'REPORT_ACTIVE_DATA_FLOW', 'ACTIVE'
        elif res.is_restore_risk:
            return 'REPORT_RESTORE_RISK', 'ACTIVE'
        elif res.is_pii_exposed:
            return 'REPORT_EXPOSED_PII', 'PRESENT'
        else:
            return 'REPORT_REMAINING_RECORD', 'PRESENT'

    @staticmethod
    def _get_remediation_for_resource(res: ResourceState) -> Tuple[str, str]:
        if res.is_active_flow:
            return 'DISABLE_DATA_FLOW', 'DISABLED'
        elif res.is_restore_risk:
            return 'BLOCK_RESTORE', 'BLOCKED'
        elif res.system_id == 'analytics_platform':
            return 'ANONYMIZE_RECORD', 'ANONYMIZED'
        elif res.system_id in ['support_platform', 'identity_service']:
            if res.data_category == 'SUPPORT_ATTACHMENT':
                return 'DELETE_RECORD', 'ABSENT'
            return 'REDACT_RECORD', 'REDACTED'
        else:
            return 'DELETE_RECORD', 'ABSENT'

    @staticmethod
    def _get_verification_for_resource(res: ResourceState) -> Tuple[str, str]:
        if res.system_id == 'security_service':
            return 'VERIFY_RECORD_PRESENT', 'PRESENT'
        elif res.system_id == 'integration_service':
            return 'VERIFY_DATA_FLOW_DISABLED', 'DISABLED'
        elif res.system_id == 'backup_service':
            return 'VERIFY_RESTORE_BLOCKED', 'BLOCKED'
        elif res.system_id == 'analytics_platform':
            return 'VERIFY_RECORD_ANONYMIZED', 'ANONYMIZED'
        elif res.system_id in ['support_platform', 'identity_service']:
            if res.data_category == 'SUPPORT_ATTACHMENT':
                return 'VERIFY_RECORD_ABSENT', 'ABSENT'
            return 'VERIFY_RECORD_REDACTED', 'REDACTED'
        else:
            return 'VERIFY_RECORD_ABSENT', 'ABSENT'

