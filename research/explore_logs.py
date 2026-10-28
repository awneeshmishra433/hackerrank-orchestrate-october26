import glob

log_files = glob.glob('dataset/evidence/logs/*.log')
print(f"Total log files: {len(log_files)}")
for lf in log_files[:5]:
    print(f"\n--- {lf} ---")
    with open(lf, encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Total lines: {len(lines)}")
        for l in lines[:5]:
            print(f"  {l.strip()}")

