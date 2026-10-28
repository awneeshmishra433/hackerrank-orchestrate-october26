import csv

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['event_type'] in ['LINK_RESOURCE_IDENTITY', 'CLASSIFY_REQUEST', 'RESTORE_BACKUP']:
            print(row)
