import csv

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in ['case_31', 'case_32']:
            print(r)
