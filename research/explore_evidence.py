import csv, json, os

print("=== EVIDENCE FILES OVERVIEW ===")
with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
    print(f"Total evidence files registered in manifest: {len(rows)}")
    for r in rows[:15]:
        print(f"  {r['file_id']}: {r['origin']} -> {r['file_path']} (captured: {r['captured_at']})")

print("\n=== EVIDENCE FILE TYPES ON DISK ===")
actual_files = []
for root, dirs, fnames in os.walk('dataset/evidence'):
    for fn in fnames:
        actual_files.append(os.path.relpath(os.path.join(root, fn), 'dataset'))

print(f"Actual files under dataset/evidence: {len(actual_files)}")
manifest_paths = set(r['file_path'].replace('\\', '/') for r in rows)
actual_paths = set(p.replace('\\', '/') for p in actual_files)

print(f"Manifest paths count: {len(manifest_paths)}")
print(f"Actual paths count: {len(actual_paths)}")
diff_m_a = manifest_paths - actual_paths
diff_a_m = actual_paths - manifest_paths
print(f"In manifest but not on disk: {len(diff_m_a)}")
print(f"On disk but not in manifest: {len(diff_a_m)}")
if diff_a_m:
    print(f"Files on disk not in manifest: {list(diff_a_m)[:5]}")

print("\n=== SAMPLE EVIDENCE CONTENTS ===")
# Let's inspect evidence_92 (frequently cited in sample output: JSON export)
ev92_path = 'dataset/evidence/records/service_resource_export_20260915_114455.json'
if os.path.exists(ev92_path):
    with open(ev92_path, encoding='utf-8') as f:
        data = json.load(f)
        print(f"evidence_92 keys: {list(data.keys()) if isinstance(data, dict) else len(data)}")
        if isinstance(data, dict):
            for k in list(data.keys())[:5]:
                print(f"  key {k}: {data[k]}")
        elif isinstance(data, list) and len(data) > 0:
            print(f"  first item: {data[0]}")

