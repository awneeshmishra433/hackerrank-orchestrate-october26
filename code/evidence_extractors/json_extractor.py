import json
import os
from typing import List, Dict, Any, Set

class JSONEvidenceExtractor:
    """
    Extracts structured records from all JSON files in dataset/evidence/records/
    """
    
    @staticmethod
    def extract_records_from_json(file_path: str, file_id: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(file_path):
            return extracted
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return extracted
        
        # Schema 1: service_resource_export with 'service_exports'
        if isinstance(data, dict) and 'service_exports' in data:
            se = data['service_exports']
            for sys_name, sys_collections in se.items():
                if isinstance(sys_collections, dict):
                    for coll_name, items in sys_collections.items():
                        if isinstance(items, list):
                            for item in items:
                                rec = JSONEvidenceExtractor._parse_item(item, fid=file_id, fpath=file_path, origin=origin, captured_at=captured_at, default_sys=sys_name)
                                if rec:
                                    extracted.append(rec)

        # Schema 2: customer_data_snapshot_bundle with 'snapshots'
        elif isinstance(data, dict) and 'snapshots' in data:
            for snap in data['snapshots']:
                sys_name = snap.get('data_store') or origin
                records = snap.get('records', [])
                for item in records:
                    rec = JSONEvidenceExtractor._parse_item(item, fid=file_id, fpath=file_path, origin=origin, captured_at=snap.get('captured_at', captured_at), default_sys=sys_name)
                    if rec:
                        extracted.append(rec)

        # Schema 3: files with 'records' list
        elif isinstance(data, dict) and 'records' in data:
            records = data.get('records', [])
            sys_name = data.get('origin') or data.get('source') or origin
            for item in records:
                rec = JSONEvidenceExtractor._parse_item(item, fid=file_id, fpath=file_path, origin=origin, captured_at=data.get('captured_at', captured_at), default_sys=sys_name)
                if rec:
                    extracted.append(rec)

        return extracted

    @staticmethod
    def _parse_item(item: Dict[str, Any], fid: str, fpath: str, origin: str, captured_at: str, default_sys: str) -> Dict[str, Any]:
        rid = item.get('resource_id')
        keys: Set[str] = set()

        for k in ['customer_reference', 'user_id', 'email', 'phone', 'email_hash', 'subject_reference', 'owner_email', 'requester_email', 'customer_email']:
            val = item.get(k)
            if val:
                keys.add(str(val).strip().lower())

        # Check nested profile
        if 'profile' in item and isinstance(item['profile'], dict):
            for pk, pv in item['profile'].items():
                if pv:
                    keys.add(str(pv).strip().lower())

        # Check nested document/hits
        if 'document' in item and isinstance(item['document'], dict):
            for dk, dv in item['document'].items():
                if dv:
                    keys.add(str(dv).strip().lower())

        if 'hits' in item and isinstance(item['hits'], dict):
            docs = item['hits'].get('documents', [])
            for d in docs:
                for dk, dv in d.items():
                    if dv:
                        keys.add(str(dv).strip().lower())
                if not rid and d.get('resource_id'):
                    rid = d.get('resource_id')

        # Determine normalized system_id
        sys_id = default_sys
        if not rid:
            return None

        # Clean system_id mapping
        if 'account' in sys_id: sys_id = 'account_service'
        elif 'search' in sys_id: sys_id = 'search_service'
        elif 'analytics' in sys_id: sys_id = 'analytics_platform'
        elif 'support' in sys_id: sys_id = 'support_platform'
        elif 'export' in sys_id: sys_id = 'export_service'
        elif 'connector' in sys_id or 'integration' in sys_id: sys_id = 'integration_service'
        elif 'backup' in sys_id: sys_id = 'backup_service'
        elif 'audit' in sys_id or 'security' in sys_id: sys_id = 'security_service'
        elif 'tombstone' in rid: sys_id = 'identity_service'

        return {
            'file_id': fid,
            'file_path': fpath,
            'captured_at': captured_at,
            'origin': origin,
            'system_id': sys_id,
            'resource_id': rid,
            'subject_keys': keys,
            'raw_item': item
        }

