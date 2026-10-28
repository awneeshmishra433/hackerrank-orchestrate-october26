import csv
from collections import Counter

cases = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

audit_dates_cases = Counter(r['audit_at'] for r in cases)
audit_dates_samples = Counter(r['audit_at'] for r in samples)

print(f"Total cases: {len(cases)}, distinct audit_at dates: {len(audit_dates_cases)}")
for d, c in audit_dates_cases.most_common(15):
    print(f"  {d}: {c} cases")

print(f"\nTotal samples: {len(samples)}, distinct audit_at dates: {len(audit_dates_samples)}")
for d, c in audit_dates_samples.most_common(15):
    print(f"  {d}: {c} samples")
