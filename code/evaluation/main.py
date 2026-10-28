import csv
import json
import os
import sys
from typing import Dict, List, Any, Tuple
from collections import Counter

def score_predictions(predictions_csv: str, ground_truth_csv: str) -> Dict[str, Any]:
    with open(predictions_csv, mode='r', encoding='utf-8') as f:
        preds = {r['case_id']: r for r in csv.DictReader(f)}

    with open(ground_truth_csv, mode='r', encoding='utf-8') as f:
        truth = {r['case_id']: r for r in csv.DictReader(f)}

    # Case-level accuracy
    total_cases = len(truth)
    correct_status = 0
    confusion_matrix = Counter()

    for cid, t_row in truth.items():
        p_row = preds.get(cid)
        t_stat = t_row['deletion_status']
        p_stat = p_row['deletion_status'] if p_row else 'MISSING'
        confusion_matrix[(t_stat, p_stat)] += 1
        if t_stat == p_stat:
            correct_status += 1

    case_status_acc = correct_status / total_cases if total_cases > 0 else 0.0

    # Step-level metrics
    total_pred_steps = 0
    total_true_steps = 0
    matched_steps = 0

    field_correct = Counter()
    total_fields = Counter()

    exact_sequence_matches = 0
    lcs_ratios = []

    for cid, t_row in truth.items():
        p_row = preds.get(cid)
        t_steps = json.loads(t_row['steps_json'])
        p_steps = json.loads(p_row['steps_json']) if p_row else []

        total_true_steps += len(t_steps)
        total_pred_steps += len(p_steps)

        # Tuples for matching: (phase, operation, system_id, resource_id, state, evidence_id)
        t_tuples = [
            (s['phase'], s['operation'], s['system_id'], s['resource_id'], s['state'], s.get('evidence_id', ''))
            for s in t_steps
        ]
        p_tuples = [
            (s['phase'], s['operation'], s['system_id'], s['resource_id'], s['state'], s.get('evidence_id', ''))
            for s in p_steps
        ]

        # Greedy or count match
        p_remaining = list(p_tuples)
        for tt in t_tuples:
            if tt in p_remaining:
                matched_steps += 1
                p_remaining.remove(tt)

        # Field-level accuracy on aligned steps
        min_len = min(len(t_steps), len(p_steps))
        for i in range(min_len):
            ts = t_steps[i]
            ps = p_steps[i]
            for fld in ['step_no', 'phase', 'operation', 'system_id', 'resource_id', 'state', 'evidence_id']:
                total_fields[fld] += 1
                if ts.get(fld) == ps.get(fld):
                    field_correct[fld] += 1

        # Extra true steps that weren't predicted count as missed fields
        for i in range(min_len, len(t_steps)):
            for fld in ['step_no', 'phase', 'operation', 'system_id', 'resource_id', 'state', 'evidence_id']:
                total_fields[fld] += 1

        # Sequence accuracy
        if t_tuples == p_tuples:
            exact_sequence_matches += 1

        # Longest Common Subsequence (LCS) ratio
        lcs_len = compute_lcs(t_tuples, p_tuples)
        denom = max(len(t_tuples), len(p_tuples), 1)
        lcs_ratios.append(lcs_len / denom)

    precision = matched_steps / total_pred_steps if total_pred_steps > 0 else 0.0
    recall = matched_steps / total_true_steps if total_true_steps > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    field_acc = {fld: field_correct[fld] / total_fields[fld] if total_fields[fld] > 0 else 0.0 for fld in total_fields}
    exact_seq_acc = exact_sequence_matches / total_cases if total_cases > 0 else 0.0
    avg_lcs_ratio = sum(lcs_ratios) / len(lcs_ratios) if lcs_ratios else 0.0

    return {
        'total_cases': total_cases,
        'case_status_accuracy': case_status_acc,
        'confusion_matrix': dict(confusion_matrix),
        'step_precision': precision,
        'step_recall': recall,
        'step_f1': f1,
        'field_level_accuracy': field_acc,
        'exact_sequence_accuracy': exact_seq_acc,
        'average_lcs_ratio': avg_lcs_ratio
    }

def compute_lcs(a: list, b: list) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])
    return dp[m][n]

if __name__ == '__main__':
    pred_path = sys.argv[1] if len(sys.argv) > 1 else 'dataset/sample_output.csv'
    truth_path = sys.argv[2] if len(sys.argv) > 2 else 'dataset/sample_output.csv'

    results = score_predictions(pred_path, truth_path)
    print("=== EVALUATION RESULTS ===")
    print(f"Total Cases: {results['total_cases']}")
    print(f"Case-Level Status Accuracy: {results['case_status_accuracy']*100:.2f}%")
    print(f"Confusion Matrix: {results['confusion_matrix']}")
    print(f"Step Precision: {results['step_precision']*100:.2f}%")
    print(f"Step Recall: {results['step_recall']*100:.2f}%")
    print(f"Step F1: {results['step_f1']*100:.2f}%")
    print(f"Field-Level Accuracy: {results['field_level_accuracy']}")
    print(f"Exact Sequence Accuracy: {results['exact_sequence_accuracy']*100:.2f}%")
    print(f"Average LCS Ratio: {results['average_lcs_ratio']*100:.2f}%")

