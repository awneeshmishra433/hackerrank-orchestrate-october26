import re
import os
from typing import List, Dict, Any, Set

class TextEvidenceExtractor:
    """
    Extracts structured handover records from .txt evidence files.
    """

    @staticmethod
    def extract_records_from_txt(file_path: str, file_id: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(file_path):
            return extracted

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str or not line_str.startswith('- '):
                        continue
                    
                    parts = [p.strip() for p in line_str[2:].split('|')]
                    if len(parts) >= 6:
                        # e.g. timestamp | system | resource_id | category | status | subject
                        event_time = parts[0]
                        sys_name = parts[1]
                        rid = parts[2]
                        category = parts[3]
                        status = parts[4]
                        subject = parts[5]

                        keys: Set[str] = set()
                        if subject and subject != 'no direct identifier':
                            keys.add(subject.strip().lower())

                        extracted.append({
                            'file_id': file_id,
                            'file_path': file_path,
                            'captured_at': event_time or captured_at,
                            'origin': origin,
                            'system_id': sys_name,
                            'resource_id': rid,
                            'data_category': category,
                            'status': status,
                            'subject_keys': keys,
                            'raw_line': line_str
                        })
        except Exception as e:
            pass

        return extracted

