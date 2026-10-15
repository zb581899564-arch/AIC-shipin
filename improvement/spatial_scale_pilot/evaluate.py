"""Post-inference CPU acceptance. References stay out of the remote model process."""
import hashlib
import base64
import json
from pathlib import Path
from geometry import candidates, iou_xyw, legal, max_width, parse_choice, parse_proposal, place

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/spatial_scale_pilot_20261011'
REF = ROOT/'reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/dev_manifest.jsonl'


def main():
    receipt_path = REPORT/'inference_receipt_v2.json'
    downloaded = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    files = downloaded['files']
    for name, record in files.items():
        raw = base64.b64decode(record['raw_base64'], validate=True)
        if hashlib.sha256(raw).hexdigest() != record['sha256'] or raw.decode('utf-8') != record['text']:
            raise ValueError('downloaded receipt SHA mismatch: '+name)
    if 'failure.json' in files:
        raise ValueError('actual inference failed; no scientific acceptance')
    if json.loads(files['inference_completion.json']['text'])['status'] != 'PASS_STATIC_INFERENCE_NOT_QUALITY':
        raise ValueError('complete inference receipt missing')
    resource = json.loads(files['resource.json']['text'])
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or resource['stop_reason'] is not None:
        raise ValueError('real resource terminal not completed')
    if downloaded['resource_unique_terminal_match'] is not True or downloaded['active_owned_job']:
        raise ValueError('GPU terminal/ledger/owned active mismatch')
    predictions = [json.loads(s) for s in files['predictions.jsonl']['text'].splitlines()]
    real_calls = [json.loads(s) for s in files['calls.jsonl']['text'].splitlines()]
    reference = [json.loads(s) for s in REF.read_text(encoding='utf-8-sig').splitlines()]
    registration = json.loads((REPORT/'execution_registration.json').read_text())
    if hashlib.sha256(REF.read_bytes()).hexdigest() != registration['reference_manifest_sha256']:
        raise ValueError('registered reference bytes changed')
    if len(predictions) != 4 or len(real_calls) != 12 or {v['item_id'] for v in predictions} != {v['item_id'] for v in reference}:
        raise ValueError('four-image/12-call denominator mismatch')
    by_id = {v['item_id']:v for v in predictions}
    values = []
    for item in reference:
        p = by_id[item['item_id']]
        W,H,ratio = item['source_width'],item['source_height'],item['target_ratio_wh']
        if p['source_sha256'] != item['media_sha256'] or p['reference_labels_read'] or p['time_selection_changed']:
            raise ValueError('source or label-isolation failure')
        calls = [c for c in real_calls if c['item_id']==item['item_id']]
        if calls != p['calls'] or [c['stage'] for c in calls] != ['BASELINE_CENTER','JOINT_PROPOSAL','CANDIDATE_RANK']:
            raise ValueError('real raw answers not exact bound')
        if any(c['input_tokens']>16384 for c in calls):raise ValueError('input contract exceeded')
        proposed_center,scale = parse_proposal(calls[1]['raw'])
        pool = candidates(p['baseline_box'],p['baseline_center'],proposed_center,scale,W,H,ratio)
        if pool != p['candidates'] or parse_choice(calls[2]['raw'],len(pool)) != p['choice']:
            raise ValueError('independent candidate/raw CPU reconstruction mismatch')
        if pool[p['choice']]['box'] != p['chosen_box']:
            raise ValueError('chosen source box differs')
        if p['center_only_box'] != place(proposed_center,max_width(W,H,ratio),W,H,ratio):
            raise ValueError('center-only control geometry differs')
        boxes=[p['baseline_box'],p['center_only_box'],p['chosen_box']]+[v['box'] for v in pool]
        if not all(legal(v,W,H,ratio) for v in boxes):raise ValueError('illegal geometry')
        target=item['reference_boxes'][0]
        base=iou_xyw(p['baseline_box'],target,ratio)
        chosen=iou_xyw(p['chosen_box'],target,ratio)
        center=iou_xyw(p['center_only_box'],target,ratio)
        oracle=max(iou_xyw(v['box'],target,ratio) for v in pool)
        values.append(dict(item_id=item['item_id'],baseline_iou=base,chosen_iou=chosen,
            center_only_iou=center,delta=chosen-base,candidate_pool_oracle_after_observation=oracle,
            selected_width=p['chosen_box'][2],baseline_width=p['baseline_box'][2],
            choice=p['choice'],seconds=p['end_to_end_seconds']))
    mean = lambda key:sum(v[key] for v in values)/len(values)
    config = json.loads(files['config.json']['text'])
    gate = config['quality_gate']
    checks=dict(mean_gain=mean('delta') >= gate['mean_iou_delta_min'],
        positive_items=sum(v['delta']>0 for v in values)>=gate['positive_items_min'],
        no_item_excessive_regression=min(v['delta'] for v in values)>=gate['per_item_delta_min'])
    result=dict(status='PASS_DEV_SCREEN_ONLY_NOT_VIDEO_OR_COMPETITION_QUALITY' if all(checks.values()) else
        'STOP_FIXED_STATIC_DEV_RECIPE_NO_HOLDOUT_NO_426',checks=checks,items=values,
        macro_baseline_iou=mean('baseline_iou'),macro_chosen_iou=mean('chosen_iou'),
        macro_center_only_iou=mean('center_only_iou'),macro_delta=mean('delta'),
        positive_items=sum(v['delta']>0 for v in values),model_calls=len(real_calls),
        gpu_job_seconds=resource['charged_seconds'],full_job_sampled_peak_mib=resource['sampled_peak_memory_mib'],
        total_output_tokens=sum(v['output_tokens'] for v in real_calls),
        inference_generate_seconds=sum(v['seconds'] for v in real_calls),
        reference_tier='GNMC_SINGLE_EDITOR_STATIC_16_9_LOCAL_NONCOMMERCIAL_DIAGNOSTIC',
        independent_video_quality=False,official_score=None,new_optimizer_updates=0,
        sealed_holdout_read=False,rematch_inference_started=False,
        receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest())
    with (REPORT/'independent_cpu_evaluation.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
