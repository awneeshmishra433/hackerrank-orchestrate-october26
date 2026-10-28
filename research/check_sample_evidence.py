import csv, json

manifest = {}
with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        manifest[r['file_id']] = r

cited_eids = set()
with open('dataset/sample_output.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for s in json.loads(r['steps_json']):
            eid = s.get('evidence_id')
            if eid:
                cited_eids.add(eid)

print(f"Distinct evidence IDs cited in samples: {len(cited_eids)}")
for eid in sorted(cited_eids):
    info = manifest.get(eid, {})
    print(f"  {eid}: {info.get('origin')} -> {info.get('file_path')}")

