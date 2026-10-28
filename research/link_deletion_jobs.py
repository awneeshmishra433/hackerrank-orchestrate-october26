import csv, json

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

# Check all activities from deletion_worker
# Let's inspect how resources are linked to accounts
# Specifically: in activities, does any activity mention the source resource or target resource?
for a in activities[:50]:
    if a['source_system'] == 'deletion_worker':
        print(f"{a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['details']}")
