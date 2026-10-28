import csv

cases = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
matching = [c for c in cases if c['reported_at'] == '2026-01-12T12:00:00Z']
print(f"Cases with reported_at = 2026-01-12T12:00:00Z: {len(matching)}")
for c in matching:
    print(f"  {c['case_id']}: email={c['email']} | req_at={c['requested_at']} | rep_stat={c['reported_status']}")
