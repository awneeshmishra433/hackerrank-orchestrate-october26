import argparse
import csv
import json
import os
import sys

# Ensure code package is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.config import (
    DEFAULT_INPUT, DEFAULT_OUTPUT, DATASET_DIR
)
from code.loaders.dataset_loader import DatasetLoader
from code.identity_resolver.resolver import IdentityResolver, IdentityProfile
from code.rule_engine.intent_classifier import IntentClassifier
from code.state_reconstructor.reconstructor import StateReconstructor, ResourceState
from code.plan_builder.builder import PlanBuilder
from code.validator.output_validator import OutputValidator

from code.evidence_extractors.json_extractor import JSONEvidenceExtractor
from code.evidence_extractors.sql_extractor import SQLEvidenceExtractor
from code.evidence_extractors.log_extractor import LogEvidenceExtractor
from code.evidence_extractors.pdf_extractor import PDFEvidenceExtractor
from code.evidence_extractors.image_extractor import ImageEvidenceExtractor
from code.evidence_extractors.txt_extractor import TextEvidenceExtractor

def build_full_evidence_catalog(manifest: dict, activities: list) -> list:
    catalog = []
    for fid, meta in manifest.items():
        fpath = os.path.join(DATASET_DIR, meta['file_path'])
        ext = os.path.splitext(fpath)[1].lower()
        if ext == '.json':
            catalog.extend(JSONEvidenceExtractor.extract_records_from_json(fpath, fid, meta['origin'], meta['captured_at']))
        elif ext == '.sql':
            catalog.extend(SQLEvidenceExtractor.extract_records_from_sql(fpath, fid, meta['origin'], meta['captured_at']))
        elif ext == '.log':
            catalog.extend(LogEvidenceExtractor.extract_records_from_log(fpath, fid, meta['origin'], meta['captured_at']))
        elif ext == '.pdf':
            catalog.extend(PDFEvidenceExtractor.extract_records_from_pdf(fpath, fid, meta['origin'], meta['captured_at']))
        elif ext == '.png':
            catalog.extend(ImageEvidenceExtractor.extract_records_from_image(fpath, fid, meta['origin'], meta['captured_at'], activities))
        elif ext == '.txt':
            catalog.extend(TextEvidenceExtractor.extract_records_from_txt(fpath, fid, meta['origin'], meta['captured_at']))
    return catalog

def run_audit(input_csv: str, output_csv: str):
    print(f"Starting Deletion Audit Pipeline...")
    print(f"Input: {input_csv}")
    print(f"Output: {output_csv}")

    loader = DatasetLoader(DATASET_DIR)
    user_identities = loader.load_user_identities()
    user_audit_logs = loader.load_user_audit_log()
    system_activities = loader.load_system_activity()
    evidence_manifest = loader.load_evidence_manifest()
    requests = loader.load_requests(input_csv)

    print(f"Loaded {len(requests)} requests to audit.")
    resolver = IdentityResolver(user_identities, user_audit_logs)

    # Pre-index activities by resource_id and by subject
    act_by_res = {}
    act_by_subject = {}
    account_deletes = []

    for a in system_activities:
        rid = a['resource_id']
        if rid not in act_by_res:
            act_by_res[rid] = []
        act_by_res[rid].append(a)

        if rid.startswith('account_') and a['event_type'] == 'DELETE_RECORD':
            account_deletes.append(a)

        det = a['details'].lower()
        for w in det.replace(',', ' ').replace(';', ' ').replace('.', ' ').split():
            if '@' in w or w.startswith('user_'):
                if w not in act_by_subject:
                    act_by_subject[w] = []
                act_by_subject[w].append(a)

    print("Building evidence catalog across all evidence files...")
    evidence_catalog = build_full_evidence_catalog(evidence_manifest, system_activities)
    print(f"Evidence catalog ready: {len(evidence_catalog)} items indexed.")

    # Sort account deletes by event_time
    account_deletes.sort(key=lambda x: x['event_time'])

    output_rows = []

    for req in requests:
        case_id = req['case_id']
        req_email = req['email']
        audit_at = req['audit_at']
        rep_at = req['reported_at']
        req_at = req['requested_at']
        request_text = req['request_text']

        # 1. Intent check
        is_auth = IntentClassifier.is_deletion_authorized(request_text)
        if not is_auth:
            output_rows.append({
                'case_id': case_id,
                'deletion_status': 'NOT_APPLICABLE',
                'steps_json': '[]'
            })
            continue

        # 2. Identity resolution
        profile = resolver.resolve(req_email)
        target_keys = set(profile.emails) | set(profile.phones) | set(profile.email_hashes)
        if profile.user_id:
            target_keys.add(profile.user_id.lower())

        # 3. Discover evidence records on or before audit_at matching this subject
        case_evidence = [
            e for e in evidence_catalog
            if e['captured_at'] <= audit_at and (e['subject_keys'] & target_keys)
        ]

        # 4. Discover activities on or before audit_at
        case_activities = []
        for k in target_keys:
            for a in act_by_subject.get(k, []):
                if a['event_time'] <= audit_at:
                    case_activities.append(a)

        # 5. Link account_id
        # Check if an account_id was already in evidence
        known_account_ids = [e['resource_id'] for e in case_evidence if e['resource_id'].startswith('account_')]

        # Check if user_id correlates to an account resource
        if not known_account_ids and profile.user_id:
            try:
                unum = int(profile.user_id.split('_')[1])
                cand1 = f"account_{unum:03d}"
                cand2 = f"account_{unum}"
                if cand1 in act_by_res or any(e['resource_id'] == cand1 for e in case_evidence):
                    known_account_ids.append(cand1)
                elif cand2 in act_by_res or any(e['resource_id'] == cand2 for e in case_evidence):
                    known_account_ids.append(cand2)
                elif unum < 100:  # Canonical primary account naming for low-index account tiers
                    known_account_ids.append(cand1)
            except:
                pass

        # Check account delete around rep_at
        if not known_account_ids and rep_at:
            best_act = None
            min_diff = 7200  # 2 hours in seconds
            for a in account_deletes:
                if a['event_time'] <= audit_at:
                    # Compare time difference
                    try:
                        # Simple string comparison or hour matching
                        if a['event_time'][:10] == rep_at[:10]: # same day
                            diff = abs(int(a['event_time'][11:13]) - int(rep_at[11:13])) * 3600
                            if diff <= min_diff:
                                best_act = a
                    except:
                        pass
            if best_act:
                known_account_ids.append(best_act['resource_id'])

        for aid in known_account_ids:
            for a in act_by_res.get(aid, []):
                if a['event_time'] <= audit_at:
                    case_activities.append(a)

        # If we have an account_id, check the deletion batch activities around its delete time
        if known_account_ids:
            aid = known_account_ids[0]
            del_acts = [a for a in act_by_res.get(aid, []) if a['event_type'] == 'DELETE_RECORD' and a['event_time'] <= audit_at]
            if del_acts:
                del_time = del_acts[0]['event_time']
                # Search activities in +/- 1 hour
                for a in system_activities:
                    if a['event_time'] <= audit_at and a['event_time'][:13] == del_time[:13]:
                        # If resource matches any known subject key or is part of case evidence
                        rid = a['resource_id']
                        if any(e['resource_id'] == rid for e in case_evidence):
                            case_activities.append(a)

        # Find latest evidence file id for this audit date to use as default citation if needed
        default_evidence_id = ""
        avail_eids = [e['file_id'] for e in case_evidence]
        if avail_eids:
            default_evidence_id = avail_eids[0]
        else:
            # Pick latest evidence file captured on or before audit_at
            cands = [fid for fid, m in evidence_manifest.items() if m['captured_at'] <= audit_at]
            if cands:
                default_evidence_id = sorted(cands, key=lambda x: evidence_manifest[x]['captured_at'])[-1]

        # 6. Reconstruct operational state
        resources = StateReconstructor.reconstruct_for_case(
            case_id=case_id,
            audit_at=audit_at,
            profile=profile,
            case_evidence=case_evidence,
            case_activities=case_activities
        )

        # 7. Build plan
        status, steps = PlanBuilder.build_plan(
            is_deletion_auth=is_auth,
            resources=resources,
            default_evidence_id=default_evidence_id
        )

        output_rows.append({
            'case_id': case_id,
            'deletion_status': status,
            'steps_json': json.dumps(steps)
        })

    # Sort output rows by case_id
    output_rows.sort(key=lambda r: r['case_id'])

    # Write output CSV
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['case_id', 'deletion_status', 'steps_json'])
        for r in output_rows:
            writer.writerow([r['case_id'], r['deletion_status'], r['steps_json']])

    print(f"Successfully generated {len(output_rows)} rows to {output_csv}")

    # Validate output
    is_valid, errors = OutputValidator.validate_file(output_csv, expected_cases=len(output_rows))
    if not is_valid:
        print(f"Validation warnings/errors ({len(errors)}):")
        for err in errors[:10]:
            print(f"  {err}")
    else:
        print("Output file passed all validation checks successfully!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ghost Data Still Exists - Deletion Audit Pipeline")
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT, help="Path to input deletion requests CSV")
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT, help="Path to output predictions CSV")
    args = parser.parse_args()

    run_audit(args.input, args.output)
