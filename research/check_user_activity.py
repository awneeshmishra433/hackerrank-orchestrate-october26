import csv

# Let's inspect system_activity rows for sample case users
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    r = list(csv.DictReader(f))

for sample_user in ['user_01', 'user_02', 'user_05', 'user_06', 'user_29', 'user_43']:
    print(f"\n=== System Activity for {sample_user} ===")
    matches = []
    for row in r:
        if sample_user in row['details'] or sample_user in row['resource_id']:
            matches.append(row)
    print(f"Total matching activities: {len(matches)}")
    for m in matches[:6]:
        print(f"  {m['event_time']} | {m['event_type']} | {m['source_system']} -> {m['target_system']} | res={m['resource_id']} | reslt={m['reported_result']} | det={m['details']}")
