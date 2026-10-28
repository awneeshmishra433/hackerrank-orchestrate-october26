import csv, json
from datetime import datetime

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
samples_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
account_deletes = [a for a in activities if a['resource_id'].startswith('account_') and a['event_type'] == 'DELETE_RECORD']

print(f"Total account deletes: {len(account_deletes)}")

for cid, steps in sorted(samples_out.items()):
    req = samples_req[cid]
    rep_at = req['reported_at']
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service'][0]
    
    matching_acts = [a for a in account_deletes if a['resource_id'] == exp_acc]
    if matching_acts:
        act = matching_acts[0]
        print(f"{cid} (rep_at={rep_at}): exp_acc={exp_acc} -> act_time={act['event_time']} | result={act['reported_result']}")
    else:
        print(f"{cid} (rep_at={rep_at}): exp_acc={exp_acc} -> NO ACTIVITY FOUND")
