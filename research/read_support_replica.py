with open('dataset/evidence/logs/support_replica.log', encoding='utf-8') as f:
    for i, l in enumerate(f):
        if i < 20:
            print(f"{i+1}: {l.strip()}")
