import csv
import os
from typing import Dict, List, Any
from code.config import DATASET_DIR

class DatasetLoader:
    def __init__(self, dataset_dir: str = DATASET_DIR):
        self.dataset_dir = dataset_dir

    def load_user_identities(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, 'user_identities.csv')
        with open(path, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_user_audit_log(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, 'user_audit_log.csv')
        with open(path, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_system_activity(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, 'system_activity.csv')
        with open(path, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_deletion_rules(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, 'deletion_rules.csv')
        with open(path, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_evidence_manifest(self) -> Dict[str, Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, 'evidence_files.csv')
        manifest = {}
        with open(path, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                manifest[row['file_id']] = row
        return manifest

    def load_requests(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

