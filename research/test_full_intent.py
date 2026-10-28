import sys, os
sys.path.insert(0, os.path.abspath('.'))
import csv
from code.rule_engine.intent_classifier import IntentClassifier

all_cases = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
non_auth = [c['case_id'] for c in all_cases if not IntentClassifier.is_deletion_authorized(c['request_text'])]
print(f"Non-authorized cases in full dataset ({len(non_auth)}): {non_auth}")
