import csv, json

outputs = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))
evidence_files = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# Collect all resources from sample_output
sample_resources = {}
for row in outputs:
    cid = row['case_id']
    steps = json.loads(row['steps_json'])
    for s in steps:
        res_id = s['resource_id']
        if res_id not in sample_resources:
            sample_resources[res_id] = []
        sample_resources[res_id].append((cid, s['phase'], s['operation'], s['system_id'], s.get('evidence_id')))

print(f"Total distinct resources across 32 samples: {len(sample_resources)}")

# Check where each resource is found:
# 1. system_activity.csv
# 2. evidence_files (content inspection)
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

act_by_res = {}
for a in activities:
    rid = a['resource_id']
    if rid not in act_by_res:
        act_by_res[rid] = []
    act_by_res[rid].append(a)

found_in_act = 0
not_in_act = []
for rid in sample_resources:
    if rid in act_by_res:
        found_in_act += 1
    else:
        not_in_act.append(rid)

print(f"Resources appearing in system_activity.csv: {found_in_act} / {len(sample_resources)}")
print(f"Resources NOT in system_activity.csv: {len(not_in_act)} -> {not_in_act[:10]}")
