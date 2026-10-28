import csv, json

# Load sample requests
requests = {}
with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        requests[row['case_id']] = row

# Load sample outputs
outputs = {}
with open('dataset/sample_output.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        outputs[row['case_id']] = {
            'deletion_status': row['deletion_status'],
            'steps': json.loads(row['steps_json'])
        }

# Load user identities
users_by_email = {}
users_by_id = {}
with open('dataset/user_identities.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        users_by_email[row['email'].lower()] = row
        users_by_id[row['user_id']] = row

# Load audit logs
audit_logs_by_user = {}
with open('dataset/user_audit_log.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        uid = row['user_id']
        if uid not in audit_logs_by_user:
            audit_logs_by_user[uid] = []
        audit_logs_by_user[uid].append(row)

# Load evidence manifest
evidence_manifest = {}
with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        evidence_manifest[row['file_id']] = row

selected_cases = ['case_01', 'case_03', 'case_05', 'case_06', 'case_09', 'case_11', 'case_13', 'case_16', 'case_21', 'case_26', 'case_29']

for cid in selected_cases:
    req = requests[cid]
    out = outputs[cid]
    email = req['email'].lower()
    user = users_by_email.get(email)
    uid = user['user_id'] if user else 'UNKNOWN'
    audits = audit_logs_by_user.get(uid, [])
    
    print(f"\n==================================================")
    print(f"CASE: {cid} | Status: {out['deletion_status']} | Reported: {req['reported_status']}")
    print(f"Email: {req['email']} | ReqAt: {req['requested_at']} | AuditAt: {req['audit_at']}")
    print(f"User: {user}")
    if audits:
        print(f"Audits for {uid}: {audits}")
    print(f"Request text: {req['request_text']}")
    print(f"Steps ({len(out['steps'])}):")
    for s in out['steps']:
        eid = s.get('evidence_id')
        ev_info = evidence_manifest.get(eid, {})
        ev_file = ev_info.get('file_path', '')
        print(f"  Step {s['step_no']}: [{s['phase']}] {s['operation']} | {s['system_id']} | {s['resource_id']} | {s['state']} | ev={eid} ({ev_file})")

