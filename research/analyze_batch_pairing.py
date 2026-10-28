import csv

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

# Group consecutive activities by deletion_worker
batches = []
cur_batch = []
for a in activities:
    if a['source_system'] == 'deletion_worker':
        cur_batch.append(a)
    else:
        if cur_batch:
            batches.append(cur_batch)
            cur_batch = []
if cur_batch:
    batches.append(cur_batch)

print(f"Total deletion worker batches: {len(batches)}")
for i, b in enumerate(batches[:10]):
    print(f"\nBatch {i+1} ({len(b)} events, from {b[0]['event_time']} to {b[-1]['event_time']}):")
    for act in b:
        print(f"   {act['event_time']} | {act['event_type']} | {act['target_system']} | {act['resource_id']} | {act['reported_result']}")
