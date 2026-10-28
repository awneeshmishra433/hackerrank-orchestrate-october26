import sqlite3, glob

sql_files = glob.glob('dataset/evidence/databases/*.sql')
for sf in sql_files:
    conn = sqlite3.connect(':memory:')
    with open(sf, encoding='utf-8') as f:
        try:
            conn.executescript(f.read())
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                cur.execute(f"PRAGMA table_info({t});")
                cols = [c[1] for c in cur.fetchall()]
                ref_cols = [c for c in cols if 'ref' in c or 'source' in c or 'account' in c or 'user' in c]
                if ref_cols:
                    print(f"{sf} -> {t}: ref_cols={ref_cols}")
        except: pass
    conn.close()
