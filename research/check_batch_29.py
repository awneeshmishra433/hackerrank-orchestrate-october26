import csv

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for i, r in enumerate(csv.DictReader(f)):
        if 3528 <= i <= 3545:
            print(f"{i}: {r['event_time']} | {r['event_type']} | {r['source_system']} -> {r['target_system']} | res={r['resource_id']} | det={r['details']}")
