"""First new ordinary/redundant deletion comparison on all original raters.

Only this CPU process opens references. No manual summary omission is treated
as ORDINARY truth. This duration-summary proxy is not the official score.
"""
import argparse
from fractions import Fraction as F
from pathlib import Path
import sys

from reference_common import (ARMS, checked, exact_metrics, frames, merged,
    metrics, read, ref, require, save, serialized, validate_gates, validate_indices)


def checked_decisions(inputs, decisions, decision_directory):
    """Bind each new parsed decision to its actual done and independent QA."""
    expected = {entry['case_id']: entry for entry in inputs['entries']}
    rows = decisions['entries']
    require([row['case_id'] for row in rows] == list(expected) and len(rows) == len(expected),
            'Complete unique new decision denominator and order required')
    require(decisions['status'] == 'COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY'
        and decisions['actual_model_calls'] == len(rows) and decisions['first_input_QA_complete'] is True
        and decisions['first_output_QA_complete'] is True and decisions['reference_labels_in_inference'] is False,
        'Complete new actual inference and first independent input/output QA required')
    terminal = read(checked(decisions['unique_gpu_terminal_ref']))
    require(terminal['status'] == 'completed' and terminal['exit_code'] == 0, 'New GPU must complete naturally')
    result = {}
    for row in rows:
        case = row['case_id']; entry = expected[case]
        dp = checked(row['decision_ref']); done = read(dp); proof = read(checked(row['output_qa_ref']))
        require(dp.is_relative_to(decision_directory), 'Actual new done escaped its new completed stage')
        require(done['case_id'] == case and proof['done_ref'] == row['decision_ref']
            and done['parsed'] == proof['parsed'] and proof['CPU_only'] is True
            and proof['status'] == 'PASS_FIRST_INDEPENDENT_OUTPUT_QA' and proof['new_model_calls'] == 0,
            'Decision differs from independently accepted actual done')
        raw = read(checked(done['raw_ref'])); actual_input = read(checked(done['input_ref']))
        first_qa = read(checked(done['first_input_qa_ref']))
        require(proof['raw_ref'] == done['raw_ref'] and proof['first_input_qa_ref'] == done['first_input_qa_ref']
            and raw['actual_model_call'] is True and raw['input_ref'] == done['input_ref']
            and raw['first_input_qa_ref'] == done['first_input_qa_ref'] and first_qa['input_ref'] == done['input_ref'],
            'Actual input/raw/first QA chain differs')
        for key in ('case_id', 'source_name', 'source_id', 'source_sha256', 'source_ordinals', 'exact_pts',
                    'window_exact', 'window_native_end_ordinal', 'window_native_end_exact', 'candidate_events', 'cache_ref', 'original_first_QA_ref'):
            require(actual_input[key] == row[key] == entry[key], 'Actual new input differs from frozen mapping: '+key)
        result[case] = validate_indices({arm: done['parsed'][arm] for arm in ARMS}, len(entry['candidate_events']))
    return result

