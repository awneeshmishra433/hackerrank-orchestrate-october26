import csv, json, os
from collections import Counter

print('=== 1. DELETION RULES ===')
with open('dataset/deletion_rules.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        print(f"{row['rule_id']}: category={row['data_category']} | condition={row['condition']} | action={row['required_action']}")

print('\n=== 2. SYSTEM ACTIVITY CATEGORICALS ===')
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    r = csv.DictReader(f)
    event_types = Counter()
    sources = Counter()
    targets = Counter()
    results = Counter()
    for row in r:
        event_types[row['event_type']] += 1
        sources[row['source_system']] += 1
        targets[row['target_system']] += 1
        results[row['reported_result']] += 1
    print('Event Types:', dict(event_types))
    print('Top Source Systems:', dict(sources.most_common(8)))
    print('Top Target Systems:', dict(targets.most_common(8)))
    print('Reported Results:', dict(results))

print('\n=== 3. USER AUDIT LOG CATEGORICALS ===')
with open('dataset/user_audit_log.csv', encoding='utf-8') as f:
    r = csv.DictReader(f)
    fields = Counter()
    for row in r:
        fields[row['field_name']] += 1
    print('Audit Log Field Names:', dict(fields))

print('\n=== 4. EVIDENCE MANIFEST CATEGORICALS ===')
with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    r = csv.DictReader(f)
    origins = Counter()
    extensions = Counter()
    for row in r:
        origins[row['origin']] += 1
        ext = os.path.splitext(row['file_path'])[1].lower()
        extensions[ext] += 1
    print('Origins:', dict(origins))
    print('Extensions:', dict(extensions))

print('\n=== 5. SAMPLE OUTPUT ANALYSIS ===')
with open('dataset/sample_output.csv', encoding='utf-8') as f:
    r = csv.DictReader(f)
    statuses = Counter()
    phases = Counter()
    operations = Counter()
    evidence_types = Counter()
    step_counts = []
    cases = []
    for row in r:
        statuses[row['deletion_status']] += 1
        steps = json.loads(row['steps_json'])
        step_counts.append(len(steps))
        cases.append((row['case_id'], row['deletion_status'], len(steps)))
        for s in steps:
            phases[s['phase']] += 1
            operations[s['operation']] += 1
            eid = s.get('evidence_id', '')
            if not eid:
                evidence_types['EMPTY'] += 1
            elif eid.startswith('evidence_'):
                evidence_types['FILE_ID'] += 1
            elif eid.startswith('act_') or eid.startswith('activity_'):
                evidence_types['ACTIVITY_ID'] += 1
            elif eid.startswith('audit_'):
                evidence_types['AUDIT_ID'] += 1
            else:
                evidence_types['OTHER:' + eid[:8]] += 1
    print('Statuses:', dict(statuses))
    print('Step counts per case: min=', min(step_counts), 'max=', max(step_counts), 'avg=', sum(step_counts)/len(step_counts))
    print('Phases:', dict(phases))
    print('Operations:', dict(operations))
    print('Evidence types:', dict(evidence_types))
    print('Sample cases overview:')
    for cid, st, cnt in cases:
        print(f"  {cid}: status={st}, steps={cnt}")

