import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from code.prototype_auditor import all_evidence
from code.identity_resolver.resolver import IdentityResolver

users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
resolver = IdentityResolver(users, audits)

# Build comprehensive subject -> account_id map from all evidence
key_to_account = {}
for e in all_evidence:
    rid = e['resource_id']
    if rid.startswith('account_'):
        for k in e['subject_keys']:
            key_to_account[k] = rid

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

matched = 0
for cid, steps in sorted(samples_out.items()):
    req = samples_req[cid]
    prof = resolver.resolve(req['email'])
    target_keys = set(prof.emails) | set([prof.user_id.lower()] if prof.user_id else [])
    
    # Try finding account_id from key_to_account
    found_acc = None
    for k in target_keys:
        if k in key_to_account:
            found_acc = key_to_account[k]
            break
            
    # Also check user_01 -> account_001
    if not found_acc and prof.user_id:
        try:
            unum = int(prof.user_id.split('_')[1])
            if unum <= 10:
                found_acc = f"account_{unum:03d}"
        except: pass
        
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service'][0]
    is_match = (found_acc == exp_acc)
    if is_match: matched += 1
    print(f"{cid}: Found={found_acc} vs Exp={exp_acc} -> Match: {is_match}")

print(f"\nTotal Account ID Matches: {matched} / 32 ({matched/32*100:.1f}%)")
