import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from code.identity_resolver.resolver import IdentityResolver
from code.rule_engine.intent_classifier import IntentClassifier
from code.evidence_extractors.json_extractor import JSONEvidenceExtractor
from code.evidence_extractors.sql_extractor import SQLEvidenceExtractor
from code.evidence_extractors.log_extractor import LogEvidenceExtractor
from code.evidence_extractors.pdf_extractor import PDFEvidenceExtractor
from code.evidence_extractors.image_extractor import ImageEvidenceExtractor
from code.evidence_extractors.txt_extractor import TextEvidenceExtractor

print("Building evidence catalog...")

manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

all_evidence = []
for fid, meta in manifest.items():
    fpath = os.path.join('dataset', meta['file_path'])
    ext = os.path.splitext(fpath)[1].lower()
    if ext == '.json':
        all_evidence.extend(JSONEvidenceExtractor.extract_records_from_json(fpath, fid, meta['origin'], meta['captured_at']))
    elif ext == '.sql':
        all_evidence.extend(SQLEvidenceExtractor.extract_records_from_sql(fpath, fid, meta['origin'], meta['captured_at']))
    elif ext == '.log':
        all_evidence.extend(LogEvidenceExtractor.extract_records_from_log(fpath, fid, meta['origin'], meta['captured_at']))
    elif ext == '.pdf':
        all_evidence.extend(PDFEvidenceExtractor.extract_records_from_pdf(fpath, fid, meta['origin'], meta['captured_at']))
    elif ext == '.png':
        all_evidence.extend(ImageEvidenceExtractor.extract_records_from_image(fpath, fid, meta['origin'], meta['captured_at'], activities))
    elif ext == '.txt':
        all_evidence.extend(TextEvidenceExtractor.extract_records_from_txt(fpath, fid, meta['origin'], meta['captured_at']))

print(f"Evidence catalog ready: {len(all_evidence)} items extracted.")

# Also index activities by resource_id
act_by_res = {}
for a in activities:
    rid = a['resource_id']
    if rid not in act_by_res:
        act_by_res[rid] = []
    act_by_res[rid].append(a)

print(f"System activities indexed for {len(act_by_res)} resources.")
