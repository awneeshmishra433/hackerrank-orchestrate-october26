import csv, json, os, glob, sqlite3
from pypdf import PdfReader
from code.identity_resolver.resolver import IdentityResolver, IdentityProfile
from code.rule_engine.intent_classifier import IntentClassifier

# 1. Load data
users = list(csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')))
audits = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
resolver = IdentityResolver(users, audits)

manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
samples_out = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))
samples_req = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

print(f"Loaded all base data. Manifest has {len(manifest)} files.")
