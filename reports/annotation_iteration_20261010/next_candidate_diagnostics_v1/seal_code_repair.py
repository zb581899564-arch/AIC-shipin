"""Append final source-identity repair; reuse successful diagnostic outputs."""
import json
from datetime import datetime,timezone
from pathlib import Path
from geometry_diagnostic import sha,write_once


def main():
    here=Path(__file__).resolve().parent
    original=here/'acceptance.json'
    record=json.loads(original.read_text())
    exposure=json.loads((here/'B_exposure.json').read_text())
    root=here.parents[2]
    relative='reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\temporal_sft8b_full_v1\\train_report_completion_01.json'
    expected='61230deef516877615720b6725d40fad3f054bacced54f85859381f2d397eed6'
    if exposure['bindings'][relative]!=expected or sha(root/relative)!=expected:
        raise ValueError('independently verified completion binding differs')
    if expected not in (here/'audit_B_exposure.py').read_text():
        raise ValueError('source-identity hardening absent')
    record.update(utc=datetime.now(timezone.utc).isoformat(),
        previous_acceptance_sha256=sha(original),
        amendment='B exposure completion receipt now pinned before reading. Current receipt byte SHA independently matched. Existing successful diagnostics are referenced unchanged, not rerun.',
        completion_fixed_SHA_before_read=True,
        source_and_result_SHAs={p.name:sha(p) for p in sorted(here.iterdir()) if p.is_file() and p.name!='acceptance_v2.json'})
    write_once(here/'acceptance_v2.json',record)
    print(json.dumps(dict(status=record['status'],final_acceptance_sha256=sha(here/'acceptance_v2.json'),successful_diagnostics_rerun=False)))


if __name__=='__main__':main()
