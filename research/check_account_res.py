import csv, json

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

users_by_email = {r['email'].lower(): r for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))

for cid, steps in samples_out.items():
    req = samples_req[cid]
    email = req['email'].lower()
    user = users_by_email.get(email)
    uid = user['user_id'] if user else None
    if not uid:
        for a in audits:
            if a['field_name'] == 'email' and a['old_value'].lower() == email:
                uid = a['user_id']
                break
    
    account_steps = [s for s in steps if s['system_id'] == 'account_service']
    for s in account_steps:
        print(f"{cid}: uid={uid} -> account_res={s['resource_id']} (op={s['operation']}, state={s['state']})")
