import os, glob, json, sqlite3, csv, re
from pypdf import PdfReader

def build_evidence_index():
    manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
    index = [] # list of {file_id, file_path, captured_at, origin, system_id, resource_id, subject_keys, status_info, raw}
    
    # 1. JSON files
    for fid, meta in manifest.items():
        fpath = os.path.join('dataset', meta['file_path'])
        if not os.path.exists(fpath): continue
        captured_at = meta['captured_at']
        origin = meta['origin']
        ext = os.path.splitext(fpath)[1].lower()
        
        if ext == '.json':
            try:
                with open(fpath, encoding='utf-8') as f:
                    data = json.load(f)
                    # Check service_exports
                    if isinstance(data, dict) and 'service_exports' in data:
                        se = data['service_exports']
                        for sys_name, sys_data in se.items():
                            # e.g. account_service -> profile_lookups
                            if isinstance(sys_data, dict):
                                for coll_name, coll_list in sys_data.items():
                                    if isinstance(coll_list, list):
                                        for item in coll_list:
                                            rid = item.get('resource_id')
                                            keys = set()
                                            for k in ['customer_reference', 'email', 'phone', 'email_hash', 'user_id', 'subject_reference', 'owner_email', 'requester_email']:
                                                val = item.get(k)
                                                if val: keys.add(str(val).strip().lower())
                                            # Check nested profile
                                            if 'profile' in item and isinstance(item['profile'], dict):
                                                for pk, pv in item['profile'].items():
                                                    if pv: keys.add(str(pv).strip().lower())
                                            # Check nested documents/queries
                                            if 'hits' in item and isinstance(item['hits'], dict):
                                                docs = item['hits'].get('documents', [])
                                                for d in docs:
                                                    for dk, dv in d.items():
                                                        if dv: keys.add(str(dv).strip().lower())
                                                    if d.get('resource_id'):
                                                        rid = d.get('resource_id')
                                            if rid:
                                                index.append({
                                                    'file_id': fid,
                                                    'file_path': meta['file_path'],
                                                    'captured_at': captured_at,
                                                    'origin': origin,
                                                    'system_id': sys_name,
                                                    'resource_id': rid,
                                                    'subject_keys': keys,
                                                    'item': item
                                                })
                    # Check list of items or other snapshot bundles
                    elif isinstance(data, list):
                        for item in data:
                            rid = item.get('resource_id')
                            sys_name = item.get('system_id') or origin
                            keys = set()
                            for k, v in item.items():
                                if v and k in ['customer_reference', 'email', 'phone', 'email_hash', 'user_id', 'subject_reference', 'owner_email', 'requester_email']:
                                    keys.add(str(v).strip().lower())
                            if rid:
                                index.append({
                                    'file_id': fid,
                                    'file_path': meta['file_path'],
                                    'captured_at': captured_at,
                                    'origin': origin,
                                    'system_id': sys_name,
                                    'resource_id': rid,
                                    'subject_keys': keys,
                                    'item': item
                                })
            except Exception as e:
                print(f"Error reading JSON {fpath}: {e}")

        elif ext == '.sql':
            try:
                conn = sqlite3.connect(':memory:')
                with open(fpath, encoding='utf-8') as f:
                    conn.executescript(f.read())
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in cur.fetchall()]
                for t in tables:
                    if t == 'snapshot_scope': continue
                    cur.execute(f"PRAGMA table_info({t});")
                    cols = [c[1] for c in cur.fetchall()]
                    cur.execute(f"SELECT * FROM {t};")
                    for row in cur.fetchall():
                        row_dict = dict(zip(cols, row))
                        rid = row_dict.get('resource_id')
                        keys = set()
                        for ck in ['customer_reference', 'user_id', 'email', 'phone', 'email_hash', 'owner_email', 'requester_email', 'subject_reference']:
                            if ck in row_dict and row_dict[ck]:
                                keys.add(str(row_dict[ck]).strip().lower())
                        
                        # Check record_json if present
                        if 'record_json' in row_dict and row_dict['record_json']:
                            try:
                                rj = json.loads(row_dict['record_json'])
                                if not rid: rid = rj.get('resource_id')
                                for rjk in ['customer_reference', 'user_id', 'email', 'phone', 'email_hash', 'owner_email', 'requester_email', 'subject_reference']:
                                    if rjk in rj and rj[rjk]:
                                        keys.add(str(rj[rjk]).strip().lower())
                            except: pass

                        sys_name = row_dict.get('origin_system')
                        if not sys_name:
                            # Infer from table name
                            if 'account' in t or 'profile' in t: sys_name = 'account_service'
                            elif 'search' in t: sys_name = 'search_service'
                            elif 'analytics' in t: sys_name = 'analytics_platform'
                            elif 'support' in t: sys_name = 'support_platform'
                            elif 'export' in t: sys_name = 'export_service'
                            elif 'connector' in t: sys_name = 'integration_service'
                            elif 'backup' in t: sys_name = 'backup_service'
                            elif 'audit' in t or 'security' in t: sys_name = 'security_service'
                            else: sys_name = origin

                        if rid:
                            index.append({
                                'file_id': fid,
                                'file_path': meta['file_path'],
                                'captured_at': captured_at,
                                'origin': origin,
                                'system_id': sys_name,
                                'resource_id': rid,
                                'subject_keys': keys,
                                'item': row_dict,
                                'table': t
                            })
                conn.close()
            except Exception as e:
                print(f"Error reading SQL {fpath}: {e}")

        elif ext == '.log':
            try:
                with open(fpath, encoding='utf-8') as f:
                    for line in f:
                        line_str = line.strip()
                        # Extract resource_id
                        rid_m = re.search(r'resource_id=[\'"]?([a-zA-Z0-9_]+)[\'"]?', line_str)
                        if rid_m:
                            rid = rid_m.group(1)
                            keys = set()
                            for m in re.finditer(r'(?:lookup_key|correlation_key|subject_reference|subject_key|email)=[\'"]?([^\s\'"]+)[\'"]?', line_str):
                                keys.add(m.group(1).strip().lower())
                            
                            sys_m = re.search(r'(?:system|service|function)=[\'"]?([a-zA-Z0-9_]+)[\'"]?', line_str)
                            sys_name = sys_m.group(1) if sys_m else origin
                            index.append({
                                'file_id': fid,
                                'file_path': meta['file_path'],
                                'captured_at': captured_at,
                                'origin': origin,
                                'system_id': sys_name,
                                'resource_id': rid,
                                'subject_keys': keys,
                                'item': line_str
                            })
            except Exception as e:
                print(f"Error reading LOG {fpath}: {e}")

        elif ext == '.pdf':
            try:
                reader = PdfReader(fpath)
                full_text = ""
                for p in reader.pages:
                    full_text += p.extract_text() + "\n"
                # Search for known pattern references
                for rid_m in re.finditer(r'(support_\d+|account_\d+|audit_record_\d+|export_\d+|user_\d+)', full_text):
                    rid = rid_m.group(1)
                    # Extract email/user_id in nearby context
                    keys = set()
                    for em in re.finditer(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', full_text):
                        keys.add(em.group(0).lower())
                    for uid in re.finditer(r'user_\d+', full_text):
                        keys.add(uid.group(0).lower())
                    
                    sys_name = origin
                    if rid.startswith('support_'): sys_name = 'support_platform'
                    elif rid.startswith('account_'): sys_name = 'account_service'
                    elif rid.startswith('audit_record_'): sys_name = 'security_service'
                    elif rid.startswith('export_'): sys_name = 'export_service'

                    index.append({
                        'file_id': fid,
                        'file_path': meta['file_path'],
                        'captured_at': captured_at,
                        'origin': origin,
                        'system_id': sys_name,
                        'resource_id': rid,
                        'subject_keys': keys,
                        'item': full_text[:200]
                    })
            except Exception as e:
                print(f"Error reading PDF {fpath}: {e}")

    print(f"Total evidence index records extracted: {len(index)}")
    return index

if __name__ == '__main__':
    idx = build_evidence_index()
