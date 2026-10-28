import csv, json, os

print("=== CHECKING REQUEST TEXT PATTERNS IN DELETION_REQUESTS.CSV ===")
non_deletion_keywords = [
    'leave the account active', 'not asking for deletion', 'keep the account as it is',
    'do not close the account', 'without removing any of my records', 'marketing lists only',
    'this is an information request', 'leave my profile and purchase history in place',
    'i want to continue using the service', "please don't delete or change anything"
]

non_del_cases = []
with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        txt = row['request_text'].lower()
        is_non_del = any(kw in txt for kw in non_deletion_keywords)
        if is_non_del:
            non_del_cases.append((row['case_id'], row['request_text']))

print(f"Total detected non-deletion cases: {len(non_del_cases)}")
for cid, txt in non_del_cases:
    print(f"  {cid}: {txt}")

