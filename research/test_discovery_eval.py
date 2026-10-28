import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from datetime import datetime, timedelta
from code.identity_resolver.resolver import IdentityResolver
from code.prototype_auditor import all_evidence, act_by_res, activities

users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
resolver = IdentityResolver(users, audits)

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Pre-index activities mentioning email or user_id
act_by_subject = {}
for a in activities:
    det = a['details'].lower()
    rid = a['resource_id']
    # Check words
    for w in det.replace(',', ' ').replace(';', ' ').replace('.', ' ').split():
        if '@' in w or w.startswith('user_'):
            if w not in act_by_subject: act_by_subject[w] = []
            act_by_subject[w].append(a)

print("Indexed activities by subject keys.")

# Evaluate discovery across 32 sample cases
total_exp = 0
total_found = 0

for cid, exp_steps in sorted(samples_out.items()):
    req = samples_req[cid]
    audit_at = req['audit_at']
    rep_at = req['reported_at']
    profile = resolver.resolve(req['email'])
    target_keys = set(profile.emails) | set(profile.phones) | set(profile.email_hashes)
    if profile.user_id: target_keys.add(profile.user_id.lower())

    exp_rids = {s['resource_id']: s for s in exp_steps}
    total_exp += len(exp_rids)

    # 1. Evidence matches up to audit_at
    discovered_rids = set()
    for e in all_evidence:
        if e['captured_at'] <= audit_at and (e['subject_keys'] & target_keys):
            discovered_rids.add(e['resource_id'])

    # 2. Activity matches on subject keys up to audit_at
    for k in target_keys:
        for a in act_by_subject.get(k, []):
            if a['event_time'] <= audit_at:
                discovered_rids.add(a['resource_id'])

    # 3. Direct account naming convention (e.g. user_01 -> account_001, user_10 -> account_010)
    if profile.user_id:
        try:
            unum = int(profile.user_id.split('_')[1])
            if unum <= 10:
                discovered_rids.add(f"account_{unum:03d}")
        except:
            pass

    # 4. Check deletion worker batch for this user around reported_at
    # If we have an account_id or subject, check the activity window
    account_ids = [r for r in discovered_rids if r.startswith('account_')]
    for aid in account_ids:
        # Find when aid was deleted
        for a in act_by_res.get(aid, []):
            if a['event_time'] <= audit_at and a['event_type'] == 'DELETE_RECORD':
                t_del = a['event_time']
                # Search activities in +/- 2 hours of t_del
                # Any resource that has matching target_keys or is part of deletion worker
                pass

    matches = discovered_rids & set(exp_rids.keys())
    total_found += len(matches)
    print(f"{cid}: Found {len(matches)}/{len(exp_rids)} -> {[s['resource_id'] for s in exp_steps]}")
    missing = set(exp_rids.keys()) - matches
    if missing:
        print(f"    Missing: {missing}")

print(f"\nOverall Resource Discovery: {total_found} / {total_exp} ({total_found/total_exp*100:.1f}%)")
