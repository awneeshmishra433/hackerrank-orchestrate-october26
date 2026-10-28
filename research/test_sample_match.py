import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from code.index_evidence import build_evidence_index
from code.identity_resolver.resolver import IdentityResolver

# Load
users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
resolver = IdentityResolver(users, audits)

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

evidence_index = build_evidence_index()

total_expected_resources = 0
found_resources = 0
missing_details = []

for cid, expected_steps in samples_out.items():
    req = samples_req[cid]
    audit_at = req['audit_at']
    profile = resolver.resolve(req['email'])
    
    # Target keys for this user
    target_keys = set(profile.emails) | set(profile.phones) | set(profile.email_hashes)
    if profile.user_id:
        target_keys.add(profile.user_id.lower())
    
    # Expected resources for this case
    expected_res = {s['resource_id']: s for s in expected_steps}
    total_expected_resources += len(expected_res)
    
    # Find candidate evidence matches at or before audit_at
    case_evidence = [
        e for e in evidence_index
        if e['captured_at'] <= audit_at and (e['subject_keys'] & target_keys)
    ]
    discovered_res = {e['resource_id'] for e in case_evidence}
    
    for rid, exp_step in expected_res.items():
        if rid in discovered_res:
            found_resources += 1
        else:
            missing_details.append((cid, rid, exp_step['system_id'], exp_step['operation']))

print(f"\nResults of direct evidence matching:")
print(f"Matched {found_resources} / {total_expected_resources} expected resource occurrences ({found_resources/total_expected_resources*100:.1f}%)")
print(f"Missing occurrences: {len(missing_details)}")
print("Sample missing:", missing_details[:10])
