import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATASET_DIR = os.path.join(REPO_ROOT, 'dataset')
EVIDENCE_DIR = os.path.join(DATASET_DIR, 'evidence')
DEFAULT_INPUT = os.path.join(DATASET_DIR, 'deletion_requests.csv')
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, 'output.csv')
SAMPLE_INPUT = os.path.join(DATASET_DIR, 'sample_deletion_requests.csv')
SAMPLE_OUTPUT = os.path.join(DATASET_DIR, 'sample_output.csv')

