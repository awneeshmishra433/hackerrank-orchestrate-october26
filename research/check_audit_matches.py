import csv

evidence = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))
cases = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

all_reqs = samples + cases
print(f"Total requests: {len(all_reqs)}")

# For each request, find all evidence files captured within 24 hours before or at audit_at
for r in samples[:15]:
    cid = r['case_id']
    aat = r['audit_at']
    matching_ev = [
        e['file_id'] + ' (' + e['file_path'] + ')'
        for e in evidence
        if e['captured_at'] <= aat and e['captured_at'][:10] == aat[:10]
    ]
    print(f"{cid} (audit_at={aat}): {matching_ev}")
