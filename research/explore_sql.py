import sqlite3, glob, os

sql_files = glob.glob('dataset/evidence/databases/*.sql')
print(f"Total SQL files: {len(sql_files)}")
table_schemas = {}

for sf in sql_files:
    fname = os.path.basename(sf)
    conn = sqlite3.connect(':memory:')
    with open(sf, encoding='utf-8') as f:
        sql_text = f.read()
    try:
        conn.executescript(sql_text)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"\n{fname}: {tables}")
        for t in tables:
            cur.execute(f"SELECT count(*) FROM {t};")
            cnt = cur.fetchone()[0]
            cur.execute(f"PRAGMA table_info({t});")
            cols = [c[1] for c in cur.fetchall()]
            print(f"  table '{t}': {cnt} rows, cols={cols}")
            if t not in table_schemas:
                table_schemas[t] = cols
                cur.execute(f"SELECT * FROM {t} LIMIT 2;")
                print(f"    sample row: {cur.fetchone()}")
    except Exception as e:
        print(f"Error reading {fname}: {e}")
    finally:
        conn.close()

