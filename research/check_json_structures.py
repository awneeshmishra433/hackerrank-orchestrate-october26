import glob, json, os

json_files = glob.glob('dataset/evidence/records/*.json')
print(f"Total JSON files: {len(json_files)}")

for jf in json_files:
    fname = os.path.basename(jf)
    with open(jf, encoding='utf-8') as f:
        try:
            d = json.load(f)
            if isinstance(d, dict):
                print(f"{fname}: dict with keys {list(d.keys())}")
            elif isinstance(d, list):
                print(f"{fname}: list of {len(d)} items, first item keys: {list(d[0].keys()) if d else 'empty'}")
        except Exception as e:
            print(f"{fname}: error {e}")
