import re
import os
import json
from typing import List, Dict, Any, Set
from collections import defaultdict

class LogEvidenceExtractor:
    """
    Extracts structured events and lookup traces from log files in dataset/evidence/logs/,
    correlating events across trace_id / requestId.
    """

    @staticmethod
    def extract_records_from_log(file_path: str, file_id: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(file_path):
            return extracted

        traces = defaultdict(lambda: {'keys': set(), 'resource_ids': set(), 'services': set(), 'raw_lines': []})
        single_lines = []

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue

                    # Extract trace_id or requestId
                    tid_m = re.search(r'(?:trace_id|requestId|correlation_id|tr)=[\'"]?([a-zA-Z0-9_\-]+)[\'"]?', line_str)
                    tid = tid_m.group(1) if tid_m else None
                    if not tid:
                        try:
                            jd = json.loads(line_str)
                            tid = jd.get('trace_id') or jd.get('requestId')
                        except:
                            pass

                    # Extract keys from this line
                    line_keys = set()
                    for m in re.finditer(r'(?:lookup_key|correlation_key|subject_reference|subject_ref|subject_key|match_key|email|user_id)=[\'"]?([^\s\'",}]+)[\'"]?', line_str):
                        line_keys.add(m.group(1).strip().lower())

                    for em in re.finditer(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', line_str):
                        line_keys.add(em.group(0).lower())

                    for uid_m in re.finditer(r'\buser_\d+\b', line_str):
                        line_keys.add(uid_m.group(0).lower())

                    # Extract resource IDs
                    line_rids = set(re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|export_\d+|tombstone_\d+)\b', line_str))

                    # Extract service/system
                    sys_m = re.search(r'(?:system|service|logger|function)=[\'"]?([a-zA-Z0-9_]+)[\'"]?', line_str)
                    sys_name = sys_m.group(1) if sys_m else origin

                    if tid:
                        traces[tid]['keys'].update(line_keys)
                        traces[tid]['resource_ids'].update(line_rids)
                        traces[tid]['services'].add(sys_name)
                        traces[tid]['raw_lines'].append(line_str)
                    else:
                        single_lines.append((line_keys, line_rids, sys_name, line_str))

            # Add correlated traces
            for tid, tdata in traces.items():
                keys = tdata['keys']
                for rid in tdata['resource_ids']:
                    sys_name = list(tdata['services'])[0] if tdata['services'] else origin
                    sys_name = LogEvidenceExtractor._normalize_system(rid, sys_name, origin)
                    extracted.append({
                        'file_id': file_id,
                        'file_path': file_path,
                        'captured_at': captured_at,
                        'origin': origin,
                        'system_id': sys_name,
                        'resource_id': rid,
                        'subject_keys': keys,
                        'trace_id': tid,
                        'raw_lines': tdata['raw_lines']
                    })

            # Add single lines
            for lkeys, lrids, lsys, lstr in single_lines:
                for rid in lrids:
                    sys_name = LogEvidenceExtractor._normalize_system(rid, lsys, origin)
                    extracted.append({
                        'file_id': file_id,
                        'file_path': file_path,
                        'captured_at': captured_at,
                        'origin': origin,
                        'system_id': sys_name,
                        'resource_id': rid,
                        'subject_keys': lkeys,
                        'raw_line': lstr
                    })

        except Exception as e:
            pass

        return extracted

    @staticmethod
    def _normalize_system(rid: str, sys_name: str, origin: str) -> str:
        if 'account' in rid or 'account' in sys_name: return 'account_service'
        elif 'search' in rid or 'search' in sys_name: return 'search_service'
        elif 'analytics' in rid or 'analytics' in sys_name: return 'analytics_platform'
        elif 'support' in rid or 'support' in sys_name: return 'support_platform'
        elif 'export' in rid or 'export' in sys_name: return 'export_service'
        elif 'data_flow' in rid or 'connector' in sys_name or 'integration' in sys_name: return 'integration_service'
        elif 'backup' in rid or 'backup' in sys_name: return 'backup_service'
        elif 'audit' in rid or 'security' in sys_name: return 'security_service'
        elif 'tombstone' in rid: return 'identity_service'
        return origin

