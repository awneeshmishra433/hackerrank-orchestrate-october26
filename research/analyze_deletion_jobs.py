import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from code.identity_resolver.resolver import IdentityResolver

users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
resolver = IdentityResolver(users, audits)

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Build mapping of resource_id -> known user_id / email from evidence
from code.prototype_auditor import all_evidence

res_to_users = {}
for e in all_evidence:
    rid = e['resource_id']
    if rid not in res_to_users:
        res_to_users[rid] = set()
    res_to_users[rid].update(e['subject_keys'])

# For each sample case, print all expected resources and where their subject keys are known
for cid, steps in sorted(samples_out.items())[:10]:
    req = samples_req[cid]
    prof = resolver.resolve(req['email'])
    print(f"\n--- {cid} (req_email={req['email']}, uid={prof.user_id}) ---")
    for s in steps:
        rid = s['resource_id']
        known_keys = res_to_users.get(rid, set())
        matches = known_keys & (set(prof.emails) | set([prof.user_id.lower()] if prof.user_id else []))
        print(f"  {s['system_id']} | {rid} | known_keys={known_keys} | matches_user={matches}")
