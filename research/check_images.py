import csv

with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['file_path'].endswith('.png'):
            print(f"{r['file_id']}: {r['origin']} -> {r['file_path']} ({r['captured_at']})")
