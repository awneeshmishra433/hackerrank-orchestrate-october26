import sys, os
sys.path.insert(0, os.path.abspath('.'))
import csv
from code.rule_engine.intent_classifier import IntentClassifier

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
for s in samples:
    auth = IntentClassifier.is_deletion_authorized(s['request_text'])
    if not auth:
        print(f"False negative: {s['case_id']}: {s['request_text']}")
