from typing import Dict, List, Any, Optional, Set
from code.identity_resolver.resolver import IdentityProfile

class ResourceState:
    def __init__(self, system_id: str, resource_id: str, data_category: str):
        self.system_id = system_id
        self.resource_id = resource_id
        self.data_category = data_category
        self.is_present = False
        self.is_pii_exposed = False
        self.is_active_flow = False
        self.is_restore_risk = False
        self.is_compliant = True
        self.evidence_id = ""
        self.evidence_time = ""
        self.latest_activity_time = ""
        self.latest_activity_type = ""
        self.latest_activity_result = ""

class StateReconstructor:
    """
    Reconstructs the true operational state of each resource at audit_at.
    """

    @staticmethod
    def reconstruct_for_case(
        case_id: str,
        audit_at: str,
        profile: IdentityProfile,
        case_evidence: List[Dict[str, Any]],
        case_activities: List[Dict[str, Any]]
    ) -> Dict[str, ResourceState]:
        
        resources: Dict[str, ResourceState] = {}

        # 1. Register resources from evidence
        for ev in case_evidence:
            rid = ev['resource_id']
            sys_id = ev['system_id']
            fid = ev['file_id']
            cap_at = ev['captured_at']
            
            if rid not in resources:
                cat = StateReconstructor._infer_category(sys_id, rid)
                resources[rid] = ResourceState(sys_id, rid, cat)
            
            res = resources[rid]
            # Track latest evidence covering this resource
            if cap_at > res.evidence_time:
                res.evidence_time = cap_at
                res.evidence_id = fid

            # Assess state from raw evidence if available
            raw = ev.get('raw_item') or {}
            raw_line = ev.get('raw_line') or ''
            raw_text = ev.get('raw_text') or ''

            # Check status indicators in evidence
            if sys_id == 'account_service':
                status = raw.get('account_status') or ''
                if status == 'ACTIVE':
                    res.is_present = True
                    res.is_compliant = False
                elif '404' in raw_line or raw.get('status_code') == 404:
                    res.is_present = False
                elif '200' in raw_line or raw.get('status_code') == 200:
                    res.is_present = True
                    res.is_compliant = False

            elif sys_id == 'search_service':
                res.is_present = True
                res.is_compliant = False

            elif sys_id == 'analytics_platform':
                # Check if email/phone still present
                email = raw.get('email')
                phone = raw.get('phone')
                if email or phone or 'IDENTIFIABLE' in raw_line:
                    res.is_pii_exposed = True
                    res.is_compliant = False

            elif sys_id == 'support_platform':
                req_email = raw.get('requester_email')
                req_phone = raw.get('requester_phone')
                if 'attachment' in rid or 'attachment' in raw_line.lower():
                    res.is_present = True
                    res.is_compliant = False
                elif req_email or req_phone or 'IDENTIFIABLE' in raw_line:
                    res.is_pii_exposed = True
                    res.is_compliant = False

            elif sys_id == 'identity_service':
                # Tombstone
                name = raw.get('name')
                email = raw.get('email')
                phone = raw.get('phone')
                if name or email or phone:
                    res.is_pii_exposed = True
                    res.is_compliant = False

            elif sys_id == 'integration_service':
                enabled = raw.get('enabled')
                if enabled is True or 'ACTIVE' in raw_line:
                    res.is_active_flow = True
                    res.is_compliant = False

            elif sys_id == 'backup_service':
                restore_allowed = raw.get('restore_allowed')
                if restore_allowed is True or 'ACTIVE' in raw_line or 'eligible="true"' in raw_line:
                    res.is_restore_risk = True
                    res.is_compliant = False

            elif sys_id == 'export_service':
                res.is_present = True
                res.is_compliant = False

        # 2. Incorporate system activities up to audit_at
        for act in sorted(case_activities, key=lambda x: x['event_time']):
            rid = act['resource_id']
            if rid not in resources:
                sys_id = act['target_system']
                sys_id = StateReconstructor._normalize_system(rid, sys_id)
                cat = StateReconstructor._infer_category(sys_id, rid)
                resources[rid] = ResourceState(sys_id, rid, cat)

            res = resources[rid]
            ev_type = act['event_type']
            result = act['reported_result']
            res.latest_activity_time = act['event_time']
            res.latest_activity_type = ev_type
            res.latest_activity_result = result

            if ev_type == 'DELETE_RECORD':
                if result == 'SUCCESS':
                    res.is_present = False
                    res.is_compliant = True
                elif result in ['FAILED', 'PARTIAL']:
                    res.is_present = True
                    res.is_compliant = False

            elif ev_type == 'SYNC_RECORD':
                # Re-creation!
                if result == 'SUCCESS':
                    res.is_present = True
                    res.is_compliant = False

            elif ev_type == 'ANONYMIZE_RECORD':
                if result == 'SUCCESS':
                    res.is_pii_exposed = False
                    res.is_compliant = True
                elif result in ['FAILED', 'PARTIAL']:
                    res.is_pii_exposed = True
                    res.is_compliant = False

            elif ev_type == 'REDACT_RECORD':
                if result == 'SUCCESS':
                    res.is_pii_exposed = False
                    res.is_compliant = True
                elif result in ['FAILED', 'PARTIAL']:
                    res.is_pii_exposed = True
                    res.is_compliant = False

            elif ev_type == 'DISABLE_DATA_FLOW':
                if result == 'SUCCESS':
                    res.is_active_flow = False
                    res.is_compliant = True
                elif result in ['FAILED', 'PARTIAL']:
                    res.is_active_flow = True
                    res.is_compliant = False

            elif ev_type == 'BLOCK_RESTORE':
                if result == 'SUCCESS':
                    res.is_restore_risk = False
                    res.is_compliant = True
                elif result in ['FAILED', 'PARTIAL']:
                    res.is_restore_risk = True
                    res.is_compliant = False

            elif ev_type == 'CHECK_DATA_FLOW':
                if 'remains enabled' in act['details']:
                    res.is_active_flow = True
                    res.is_compliant = False

            elif ev_type == 'CHECK_RESTORE_ACCESS':
                if 'can still be restored' in act['details']:
                    res.is_restore_risk = True
                    res.is_compliant = False

        return resources

    @staticmethod
    def _normalize_system(rid: str, sys_name: str) -> str:
        if 'account' in rid or 'account' in sys_name: return 'account_service'
        elif 'search' in rid or 'search' in sys_name: return 'search_service'
        elif 'analytics' in rid or 'analytics' in sys_name: return 'analytics_platform'
        elif 'support' in rid or 'support' in sys_name: return 'support_platform'
        elif 'export' in rid or 'export' in sys_name: return 'export_service'
        elif 'data_flow' in rid or 'connector' in sys_name or 'integration' in sys_name: return 'integration_service'
        elif 'backup' in rid or 'backup' in sys_name: return 'backup_service'
        elif 'audit' in rid or 'security' in sys_name: return 'security_service'
        elif 'tombstone' in rid: return 'identity_service'
        return sys_name

    @staticmethod
    def _infer_category(sys_id: str, rid: str) -> str:
        if sys_id == 'account_service': return 'USER_PROFILE'
        elif sys_id == 'search_service': return 'SEARCH_INDEX_ENTRY'
        elif sys_id == 'analytics_platform': return 'ANALYTICS_PROFILE'
        elif sys_id == 'support_platform':
            return 'SUPPORT_ATTACHMENT' if 'attachment' in rid else 'SUPPORT_MESSAGE'
        elif sys_id == 'export_service': return 'USER_EXPORT'
        elif sys_id == 'integration_service': return 'DATA_FLOW'
        elif sys_id == 'backup_service': return 'BACKUP_ARCHIVE'
        elif sys_id == 'security_service': return 'SECURITY_AUDIT_LOG'
        elif sys_id == 'identity_service': return 'ACCOUNT_TOMBSTONE'
        return 'UNKNOWN'

