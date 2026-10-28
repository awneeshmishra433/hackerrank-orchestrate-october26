import sys, os
sys.path.insert(0, os.path.abspath('.'))
import csv
from code.prototype_auditor import all_evidence

users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))

uid_to_account = {}
for e in all_evidence:
    rid = e['resource_id']
    if rid.startswith('account_'):
        for k in e['subject_keys']:
            if k.startswith('user_'):
                uid_to_account[k] = rid
            elif '@' in k:
                uid_to_account[k] = rid

print(f"Direct evidence mappings from user/email to account_*: {len(uid_to_account)}")
