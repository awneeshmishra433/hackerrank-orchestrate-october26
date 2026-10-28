import sqlite3
import json
import os
from typing import List, Dict, Any, Set

class SQLEvidenceExtractor:
    """
    Executes and extracts structured records from SQL snapshot files using SQLite in-memory databases.
    """

    @staticmethod
    def extract_records_from_sql(file_path: str, file_id: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(file_path):
            return extracted

        try:
            conn = sqlite3.connect(':memory:')
            with open(file_path, mode='r', encoding='utf-8') as f:
                conn.executescript(f.read())
            
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]

            for t in tables:
                if t == 'snapshot_scope':
                    continue

                cur.execute(f"PRAGMA table_info({t});")
                cols = [c[1] for c in cur.fetchall()]
                cur.execute(f"SELECT * FROM {t};")

                for row in cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    rid = row_dict.get('resource_id')
                    keys: Set[str] = set()

                    for ck in ['customer_reference', 'user_id', 'email', 'phone', 'email_hash', 'owner_email', 'requester_email', 'subject_reference', 'customer_email']:
                        val = row_dict.get(ck)
                        if val:
                            keys.add(str(val).strip().lower())

                    # Check nested record_json
                    if 'record_json' in row_dict and row_dict['record_json']:
                        try:
                            rj = json.loads(row_dict['record_json'])
                            if not rid:
                                rid = rj.get('resource_id')
                            for rjk in ['customer_reference', 'user_id', 'email', 'phone', 'email_hash', 'owner_email', 'requester_email', 'subject_reference', 'customer_email']:
                                if rjk in rj and rj[rjk]:
                                    keys.add(str(rj[rjk]).strip().lower())
                        except:
                            pass

                    if not rid:
                        continue

                    # Determine system_id
                    sys_name = row_dict.get('origin_system')
                    if not sys_name and 'record_json' in row_dict and isinstance(row_dict['record_json'], dict):
                        sys_name = row_dict['record_json'].get('origin_system')
                    
                    if not sys_name:
                        if 'account' in t or 'profile' in t: sys_name = 'account_service'
                        elif 'search' in t: sys_name = 'search_service'
                        elif 'analytics' in t: sys_name = 'analytics_platform'
                        elif 'support' in t: sys_name = 'support_platform'
                        elif 'export' in t: sys_name = 'export_service'
                        elif 'connector' in t or 'integration' in t: sys_name = 'integration_service'
                        elif 'backup' in t: sys_name = 'backup_service'
                        elif 'audit' in t or 'security' in t: sys_name = 'security_service'
                        elif 'tombstone' in rid: sys_name = 'identity_service'
                        else: sys_name = origin

                    # Normalize system_id
                    if 'account' in sys_name: sys_name = 'account_service'
                    elif 'search' in sys_name: sys_name = 'search_service'
                    elif 'analytics' in sys_name: sys_name = 'analytics_platform'
                    elif 'support' in sys_name: sys_name = 'support_platform'
                    elif 'export' in sys_name: sys_name = 'export_service'
                    elif 'connector' in sys_name or 'integration' in sys_name: sys_name = 'integration_service'
                    elif 'backup' in sys_name: sys_name = 'backup_service'
                    elif 'audit' in sys_name or 'security' in sys_name: sys_name = 'security_service'
                    elif 'tombstone' in rid: sys_name = 'identity_service'

                    extracted.append({
                        'file_id': file_id,
                        'file_path': file_path,
                        'captured_at': captured_at,
                        'origin': origin,
                        'system_id': sys_name,
                        'resource_id': rid,
                        'subject_keys': keys,
                        'table': t,
                        'raw_item': row_dict
                    })

            conn.close()
        except Exception as e:
            pass

        return extracted

