import csv, json, os, glob

# Load data
requests = {}
with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        requests[row['case_id']] = row

outputs = {}
with open('dataset/sample_output.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        outputs[row['case_id']] = {
            'deletion_status': row['deletion_status'],
            'steps': json.loads(row['steps_json'])
        }

users_by_email = {}
users_by_id = {}
with open('dataset/user_identities.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        users_by_email[row['email'].lower()] = row
        users_by_id[row['user_id']] = row

audit_logs = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
system_activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
evidence_files = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
rules = {r['rule_id']: r for r in csv.DictReader(open('dataset/deletion_rules.csv', encoding='utf-8'))}

print(f"Loaded {len(requests)} sample requests and {len(outputs)} sample outputs.")

# Function to resolve all identifiers for an email
def resolve_identity(req_email):
    norm_email = req_email.strip().lower()
    user = users_by_email.get(norm_email)
    uid = user['user_id'] if user else None
    
    # If not found directly, check audit log
    if not uid:
        for a in audit_logs:
            if a['field_name'] == 'email' and a['old_value'].strip().lower() == norm_email:
                uid = a['user_id']
                user = users_by_id.get(uid)
                break
    
    # Also check if new_value in audit log matches
    if not uid:
        for a in audit_logs:
            if a['field_name'] == 'email' and a['new_value'].strip().lower() == norm_email:
                uid = a['user_id']
                user = users_by_id.get(uid)
                break

    emails = set()
    phones = set()
    email_hashes = set()
    names = set()
    
    if user:
        if user.get('email'): emails.add(user['email'].strip().lower())
        if user.get('phone'): phones.add(user['phone'].strip())
        if user.get('email_hash'): email_hashes.add(user['email_hash'].strip().lower())
        if user.get('name'): names.add(user['name'].strip())

    emails.add(norm_email)

    if uid:
        for a in audit_logs:
            if a['user_id'] == uid:
                fn = a['field_name']
                if fn == 'email':
                    if a.get('old_value'): emails.add(a['old_value'].strip().lower())
                    if a.get('new_value'): emails.add(a['new_value'].strip().lower())
                elif fn == 'phone':
                    if a.get('old_value'): phones.add(a['old_value'].strip())
                    if a.get('new_value'): phones.add(a['new_value'].strip())
                elif fn == 'email_hash':
                    if a.get('old_value'): email_hashes.add(a['old_value'].strip().lower())
                    if a.get('new_value'): email_hashes.add(a['new_value'].strip().lower())

    return {
        'user_id': uid,
        'emails': emails,
        'phones': phones,
        'email_hashes': email_hashes,
        'names': names
    }

# Trace each sample case
traces = []
for cid in sorted(requests.keys(), key=lambda x: int(x.split('_')[1])):
    req = requests[cid]
    out = outputs[cid]
    audit_at = req['audit_at']
    ident = resolve_identity(req['email'])
    
    print(f"\n=======================================================")
    print(f"CASE {cid}: {out['deletion_status']} (reported: {req['reported_status']})")
    print(f"  Subject: uid={ident['user_id']}, emails={ident['emails']}")
    print(f"  Audit Cutoff: {audit_at}")
    
    # Check steps
    for s in out['steps']:
        phase = s['phase']
        op = s['operation']
        sys_id = s['system_id']
        res_id = s['resource_id']
        state = s['state']
        eid = s.get('evidence_id', '')
        
        # What evidence file is cited?
        ev_file_info = evidence_files.get(eid, {})
        file_path = ev_file_info.get('file_path', '')
        captured_at = ev_file_info.get('captured_at', '')
        origin = ev_file_info.get('origin', '')
        
        # Check system activities relating to this resource up to audit_at
        rel_acts = [
            a for a in system_activities
            if a['resource_id'] == res_id and a['event_time'] <= audit_at
        ]
        latest_act = rel_acts[-1] if rel_acts else None
        
        print(f"  [{phase}] {op} | {sys_id} | {res_id} | {state} | ev={eid} ({file_path})")
        if latest_act:
            print(f"      -> Latest Activity: {latest_act['event_time']} | {latest_act['event_type']} | {latest_act['reported_result']} | {latest_act['details']}")
