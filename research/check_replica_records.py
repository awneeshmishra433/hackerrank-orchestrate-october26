import sqlite3, glob, json

sql_files = glob.glob('dataset/evidence/databases/*replica*.sql')
print(f"Total replica SQL files: {len(sql_files)}")

user_counts = 0
total_records = 0

for sf in sql_files:
    conn = sqlite3.connect(':memory:')
    with open(sf, encoding='utf-8') as f:
        try:
            conn.executescript(f.read())
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                if 'customer_data' in t:
                    cur.execute(f"SELECT record_json FROM {t};")
                    for row in cur.fetchall():
                        total_records += 1
                        if row[0]:
                            try:
                                d = json.loads(row[0])
                                if d.get('customer_reference') or d.get('user_id') or d.get('subject_reference') or d.get('email'):
                                    user_counts += 1
                            except: pass
        except: pass
    conn.close()

print(f"Replica records with user reference or email: {user_counts} / {total_records}")
