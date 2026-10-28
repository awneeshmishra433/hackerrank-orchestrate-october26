import csv, json

with open('code/evaluation/sample_pred.csv', encoding='utf-8') as f:
    preds = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/sample_output.csv', encoding='utf-8') as f:
    truth = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    reqs = {r['case_id']: r for r in csv.DictReader(f)}

for cid in sorted(truth.keys()):
    p_stat = preds[cid]['deletion_status']
    t_stat = truth[cid]['deletion_status']
    if p_stat != t_stat:
        print(f"\nDiscrepancy {cid}: Pred={p_stat} vs Truth={t_stat}")
        print(f"Request: {reqs[cid]['request_text']}")
        print(f"Truth steps: {json.loads(truth[cid]['steps_json'])}")
        print(f"Pred steps: {json.loads(preds[cid]['steps_json'])}")
