"""Record actual completed proposal tools and usage; never admit labels automatically."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

root = Path(__file__).resolve().parent / 'slot6_silver24_v1'
jobs = json.loads((root / 'observations/jobs.json').read_text())['jobs']
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
rows = []
usage = {}
for name in jobs[:4]:
    folder = Path(name)
    attempt = folder / 'teacher_attempt01_http1'
    audit = json.loads((attempt / 'audit.json').read_text())
    terminal = json.loads((attempt / 'terminal.json').read_text())
    proposal = json.loads((attempt / 'proposal.json').read_text())
    assert audit['actual_result_status'] == 'SUCCESS'
    for key, value in audit['actual_result_usage'].items():
        usage[key] = usage.get(key, 0) + value
    rows.append(dict(
        window_id=audit['window_id'], actual_model=audit['actual_model'],
        result_status=audit['actual_result_status'],
        original_pngs_delivered=audit['original_pngs_delivered'],
        student_effective_pngs_delivered=audit['effective_pngs_delivered'],
        correct_native_clip_delivered=audit['native_video_delivered'],
        completed_tool_count=audit['actual_completed_tool_count'],
        client_elapsed_seconds=terminal['elapsed_seconds'],
        usage=audit['actual_result_usage'],
        proposal_sha256=audit['proposal_sha256'],
        audit_sha256=sha(attempt / 'audit.json'),
        tool_issues=audit['tool_issues'],
        geometry_identity_issues=audit['proposal_geometry_identity_issues'],
        raw_event_descriptions=len(proposal.get('events', [])),
        consequential_unknown_coverage=audit['consequential_unknown_coverage'],
        training_admitted=False,
    ))
record = dict(
    status='FOUR_REAL_PROPOSALS_COMPLETE_LABEL_ADMISSION_PENDING',
    utc=datetime.now(timezone.utc).isoformat(),
    approved_model_mode='gemini-3.8-flash-high; web 3.8 Flash 高点/超级详尽 explicitly approved',
    source_window_plan_sha256=sha(root / 'source_window_plan.json'),
    frozen_protocol_sha256=sha(root / 'frozen_protocol_v2_explicit_empty_gate.json'),
    successful_new_teacher_sessions=4,
    completed_tools=sum(r['completed_tool_count'] for r in rows),
    delivered_original_pngs=sum(r['original_pngs_delivered'] for r in rows),
    delivered_effective_pngs=sum(r['student_effective_pngs_delivered'] for r in rows),
    aggregate_reported_usage=usage,
    usage_price_known=False, cash_cost_not_fabricated=True,
    client_elapsed_not_linux_GPU_charge=True,
    tensor_views_prepared_windows=24,
    new_optimizer_updates=0, new_temporal_student_calls=0,
    new_spatial_calls=0, source_upload_done=False,
    old_failed_and_successful_attempts_preserved_not_recounted_here=True,
    success_not_semantic_quality=True, rows=rows,
)
output = root / 'pilot_execution_receipt_v1.json'
with output.open('x', encoding='utf-8') as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
print(json.dumps({k:v for k,v in record.items() if k != 'rows'}, ensure_ascii=False))
