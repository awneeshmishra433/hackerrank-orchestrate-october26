import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from code.identity_resolver.resolver import IdentityResolver
from code.prototype_auditor import all_evidence, act_by_res

users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
resolver = IdentityResolver(users, audits)

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Compare discovered resources vs sample output resources
correct_cases = 0
total_steps_matched = 0
total_expected_steps = 0

for cid, exp_steps in sorted(samples_out.items()):
    req = samples_req[cid]
    audit_at = req['audit_at']
    profile = resolver.resolve(req['email'])
    target_keys = set(profile.emails) | set(profile.phones) | set(profile.email_hashes)
    if profile.user_id: target_keys.add(profile.user_id.lower())

    # Find evidence matching target_keys captured on or before audit_at
    matching_ev = [
        e for e in all_evidence
        if e['captured_at'] <= audit_at and (e['subject_keys'] & target_keys)
    ]
    
    ev_rids = {e['resource_id']: e for e in matching_ev}
    exp_rids = {s['resource_id']: s for s in exp_steps}
    
    total_expected_steps += len(exp_steps)
    matches = set(ev_rids.keys()) & set(exp_rids.keys())
    
    print(f"{cid} (audit_at={audit_at}): Expected {len(exp_rids)} resources: {sorted(list(exp_rids.keys()))}")
    print(f"      Matched in evidence ({len(matches)}/{len(exp_rids)}): {sorted(list(matches))}")
    missing = set(exp_rids.keys()) - matches
    if missing:
        print(f"      MISSING from evidence: {sorted(list(missing))}")
        for m in missing:
            # Check if missing is in activities
            acts = act_by_res.get(m, [])
            act_times = [a['event_time'] for a in acts if a['event_time'] <= audit_at]
            print(f"         {m}: in activities up to audit_at? {len(act_times)} times: {act_times}")
