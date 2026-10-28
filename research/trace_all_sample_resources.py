import csv, json, os, glob, sqlite3, re

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

users_by_email = {r['email'].lower(): r for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}
users_by_id = {r['user_id']: r for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))

evidence_manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# For each sample case, for each step resource, find all evidence and activity mentioning that resource
for cid, steps in sorted(samples_out.items()):
    req = samples_req[cid]
    email = req['email'].lower()
    user = users_by_email.get(email)
    uid = user['user_id'] if user else None
    if not uid:
        for a in audits:
            if a['field_name'] == 'email' and a['old_value'].lower() == email:
                uid = a['user_id']
                break
    
    print(f"\n=== Case {cid} (uid={uid}, email={email}) ===")
    for s in steps:
        rid = s['resource_id']
        sys_id = s['system_id']
        eid = s.get('evidence_id', '')
        
        # Check what mentions rid
        mentions = []
        if eid and eid in evidence_manifest:
            fpath = evidence_manifest[eid]['file_path']
            mentions.append(f"cited: {eid} ({fpath})")
        
        print(f"  Resource {rid} ({sys_id}): {mentions}")
