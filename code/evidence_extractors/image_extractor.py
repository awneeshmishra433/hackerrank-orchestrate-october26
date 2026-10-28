import os
from typing import List, Dict, Any, Set

class ImageEvidenceExtractor:
    """
    Extracts evidence mappings for console screenshots based on their system origin,
    timestamps, and correlated data catalog activity.
    """

    @staticmethod
    def extract_records_from_image(file_path: str, file_id: str, origin: str, captured_at: str, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(file_path):
            return extracted

        # Find linked activity within a close time window (+/- 10 minutes)
        for act in activities:
            if act['event_type'] == 'LINK_RESOURCE_IDENTITY':
                # Check if activity event_time is right after captured_at
                act_time = act['event_time']
                if act_time >= captured_at and act_time[:13] == captured_at[:13]: # same hour
                    rid = act['resource_id']
                    details = act['details']
                    sys_name = act['target_system']
                    keys: Set[str] = set()

                    # Extract words from details
                    for word in details.replace(',', ' ').replace(';', ' ').replace('.', ' ').split():
                        if '@' in word:
                            keys.add(word.strip().lower())
                        elif word.startswith('user_'):
                            keys.add(word.strip().lower())

                    extracted.append({
                        'file_id': file_id,
                        'file_path': file_path,
                        'captured_at': captured_at,
                        'origin': origin,
                        'system_id': sys_name,
                        'resource_id': rid,
                        'subject_keys': keys,
                        'details': details
                    })

        return extracted

