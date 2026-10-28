import re
import os
from typing import List, Dict, Any, Set
from pypdf import PdfReader

class PDFEvidenceExtractor:
    """
    Extracts text and structured entities from PDF evidence documents.
    """

    @staticmethod
    def extract_records_from_pdf(file_path: str, file_id: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
        extracted = []
        if not os.path.exists(file_path):
            return extracted

        try:
            reader = PdfReader(file_path)
            full_text = ""
            for p in reader.pages:
                full_text += p.extract_text() + "\n"

            # Find all resource IDs in PDF
            rids = set(re.findall(r'\b(support_\d+|account_\d+|audit_record_\d+|export_\d+|user_\d+)\b', full_text))
            
            # Find all emails in PDF
            emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', full_text))
            uids = set(re.findall(r'\buser_\d+\b', full_text))

            keys: Set[str] = set([e.lower() for e in emails]) | set([u.lower() for u in uids])

            for rid in rids:
                if rid.startswith('user_'):
                    continue  # skip user_id as a resource_id
                
                sys_name = origin
                if rid.startswith('support_'): sys_name = 'support_platform'
                elif rid.startswith('account_'): sys_name = 'account_service'
                elif rid.startswith('audit_record_'): sys_name = 'security_service'
                elif rid.startswith('export_'): sys_name = 'export_service'

                extracted.append({
                    'file_id': file_id,
                    'file_path': file_path,
                    'captured_at': captured_at,
                    'origin': origin,
                    'system_id': sys_name,
                    'resource_id': rid,
                    'subject_keys': keys,
                    'raw_text': full_text[:400]
                })
        except Exception as e:
            pass

        return extracted

