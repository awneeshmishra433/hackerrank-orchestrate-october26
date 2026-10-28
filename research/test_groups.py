import sys, os
sys.path.insert(0, os.path.abspath('.'))

import csv, json
from code.prototype_auditor import activities

# Let's inspect all deletion_worker contiguous groups in system_activity.csv
print(f"Total activities: {len(activities)}")

del_acts = [a for a in activities if a['source_system'] == 'deletion_worker' or a['event_type'] in ['DELETE_RECORD', 'ANONYMIZE_RECORD', 'REDACT_RECORD', 'DISABLE_DATA_FLOW', 'BLOCK_RESTORE']]
print(f"Total deletion/policy activities: {len(del_acts)}")
