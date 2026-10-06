from pathlib import Path
import json,statistics
R=Path('/home/inspur/aic_video_work')
paths={'base':R/'runs/improvement_test174_multi_reader_v1/status.jsonl','lora':R/'training_round2_20260910/test_adapter_reader_v2/status.jsonl'}
result={}
for name,p in paths.items():
 rows=[json.loads(x) for x in p.read_text().splitlines()]
 coverage=[r['n_predictions']/r['metadata']['n_frames'] for r in rows]
 result[name]={'videos':len(rows),'mean_selected_frame_fraction':statistics.mean(coverage),'median_selected_frame_fraction':statistics.median(coverage),'at_least_90pct_videos':sum(x>=.9 for x in coverage),'at_least_99pct_videos':sum(x>=.99 for x in coverage),'frames':sum(r['n_predictions'] for r in rows)}
result['interpretation']='Unlabeled aggregate behavior diagnostic only; no test ground truth, manual labels, per-video corrections or score estimation.'
(R/'round3_20260912/test_aggregate_behavior.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
