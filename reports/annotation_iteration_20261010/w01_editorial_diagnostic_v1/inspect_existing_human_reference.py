"""Post-seal W01 audit only; not a new training target or a blind evaluation."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,zipfile,statistics
ROOT=Path(__file__).resolve().parent
DATA=Path(r'G:\ai\AIC视频\reports\gemini_distillation_data_20261009\data\tvsum\ydata-tvsum50-v1_1')
manifest=json.loads((ROOT.parent/'slot6_silver24_v1/observations/00_kLxoNp-UchI_W01/manifest.json').read_text(encoding='utf-8-sig'))
with zipfile.ZipFile(DATA/'ydata-tvsum50-data.zip') as archive:
    raw=archive.read('data/ydata-tvsum50-anno.tsv')
    selected=[line.split('\t') for line in raw.decode('utf-8-sig').splitlines() if line.split('\t',1)[0]==manifest['source_id']]
    ratings=[[int(v) for v in fields[2].split(',') if v.strip()] for fields in selected]
    info=[line for line in archive.read('data/ydata-tvsum50-info.tsv').decode('utf-8-sig').splitlines() if manifest['source_id'] in line.split('\t')]
report=dict(status='EXISTING_W01_HUMAN_RATINGS_POST_SEAL_DIAGNOSTIC_ONLY',source_id=manifest['source_id'],role=manifest['role'],human_rows=len(ratings),
    vector_lengths=sorted({len(row) for row in ratings}),source_total_frames=manifest['source_total_frames'],original_metadata_lines=info,
    archive_sha256=hashlib.sha256((DATA/'ydata-tvsum50-data.zip').read_bytes()).hexdigest(),
    time_mapping='SOURCE_ORDINAL_INDEX_HYPOTHESIS_ONLY; equal vector length is not proof of exact native-PTS alignment',
    original_B_prior_exposure='NOT_AUDITED_HERE',official_AIC_objective_equivalence='UNKNOWN',training_admitted=False,
    new_labels_produced=False,new_models=0,new_optimizer_updates=0)
if len(ratings)==20 and all(len(row)==manifest['source_total_frames'] for row in ratings):
    means=[statistics.mean(row[i] for row in ratings) for i in range(manifest['source_total_frames'])]
    allmean=statistics.mean(means);sampled=[]
    for f in manifest['frames']:
        sampled.append(dict(frame_id=f['frame_id'],source_ordinal=f['source_ordinal'],global_seconds_exact=f['global_seconds_exact'],hypothetical_mean_importance=means[f['source_ordinal']]))
    comparisons={}
    for side in ('teacher','independent'):
        doc=json.loads((ROOT/side/'student_sealed.json').read_text(encoding='utf-8-sig'))
        bylabel={label:[] for label in ('KEEP','NO','UNKNOWN')}
        for f in sampled:
            t=Fraction(f['global_seconds_exact'])-30
            row=next(r for r in doc['window_coverage'] if Fraction(r['start'])<=t<Fraction(r['end']))
            bylabel[row['label']].append(f['hypothetical_mean_importance'])
        comparisons[side]={lab:dict(sampled_frames=len(vals),mean=statistics.mean(vals) if vals else None,min=min(vals) if vals else None,max=max(vals) if vals else None) for lab,vals in bylabel.items()}
    report.update(sampled_ratings=sampled,hypothetical_full_source_mean=allmean,post_seal_comparison=comparisons,
        warning='No threshold, ranking cutoff, selection or reference admission is inferred from these means. Existing human importance is not gold for AIC, and this source is already exposed.')
with (ROOT/'existing_human_reference_inspection_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='sampled_ratings'},ensure_ascii=False))
