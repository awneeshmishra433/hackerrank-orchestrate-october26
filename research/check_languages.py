import csv

texts = []
with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        texts.append((row['case_id'], row['request_text']))

print(f"Total requests: {len(texts)}")
# Let's inspect unique texts or patterns
unique_texts = set(t[1] for t in texts)
print(f"Unique request texts: {len(unique_texts)}")

# Print texts that do not contain deletion words in various languages:
# English: delete, erase, close, remove
# French: suppression, supprimer
# Spanish/Portuguese: exclusão, eliminación, eliminar
# Japanese: 削除
# Korean: 삭제
deletion_markers = ['delete', 'erase', 'close', 'remove', 'suppress', 'supprimer', 'exclusão', 'eliminación', 'eliminar', '削除', '삭제']

not_obviously_del = []
for cid, t in texts:
    lower_t = t.lower()
    if not any(m in lower_t for m in deletion_markers):
        not_obviously_del.append((cid, t))

print(f"Requests without standard deletion keywords: {len(not_obviously_del)}")
for cid, t in not_obviously_del:
    print(f"  {cid}: {t}")

