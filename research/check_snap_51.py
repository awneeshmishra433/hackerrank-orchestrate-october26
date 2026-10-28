import json

with open('dataset/evidence/records/customer_data_snapshot_bundle_20260915.json', encoding='utf-8') as f:
    d = json.load(f)

for snap in d.get('snapshots', []):
    for r in snap.get('records', []):
        r_str = json.dumps(r)
        if '542' in r_str or 'kofi' in r_str:
            print(f"{snap.get('data_store')}: {r}")
