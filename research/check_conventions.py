import csv, json
from collections import defaultdict

outputs = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))

op_states = defaultdict(set)
system_resources = defaultdict(set)
system_ops = defaultdict(set)

for row in outputs:
    steps = json.loads(row['steps_json'])
    for s in steps:
        op_states[(s['phase'], s['operation'])].add(s['state'])
        res_prefix = s['resource_id'].split('_')[0]
        system_resources[s['system_id']].add(res_prefix)
        system_ops[s['system_id']].add(s['operation'])

print("=== ALLOWED (PHASE, OPERATION) -> STATES IN SAMPLES ===")
for (phase, op), states in sorted(op_states.items()):
    print(f"  [{phase}] {op} -> {states}")

print("\n=== SYSTEM_ID -> RESOURCE PREFIXES ===")
for sys_id, prefixes in sorted(system_resources.items()):
    print(f"  {sys_id} -> {sorted(prefixes)}")

print("\n=== SYSTEM_ID -> OPERATIONS ===")
for sys_id, ops in sorted(system_ops.items()):
    print(f"  {sys_id} -> {sorted(ops)}")
