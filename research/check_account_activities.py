import csv

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
account_acts = [a for a in activities if a['resource_id'].startswith('account_')]
print(f"Total activity events on account_* resources: {len(account_acts)}")
unique_accounts = set(a['resource_id'] for a in account_acts)
print(f"Unique account_* resources: {len(unique_accounts)}")

# Check event types on account_* resources
from collections import Counter
event_types = Counter(a['event_type'] for a in account_acts)
print(f"Event types on accounts: {dict(event_types)}")
