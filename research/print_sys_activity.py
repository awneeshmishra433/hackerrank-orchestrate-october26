import csv

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for i, row in enumerate(csv.DictReader(f)):
        if i >= 20: break
        print(row)
