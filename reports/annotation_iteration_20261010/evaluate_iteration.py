"""Independent full-denominator source-paired quality and native interval audit."""
import collections,hashlib,json,math
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;OLD=H.parent/'qwen8b_annotation_20261009_v1/training_v2'
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rank(v):
    values=np.array(v);order=np.argsort(values,kind='stable');out=np.empty(len(v));first=0
    while first<len(v):
        end=first+1
        while end<len(v) and values[order[end]]==values[order[first]]:end+=1
        out[order[first:end]]=(first+end-1)/2;first=end
    return out
def rho(a,b):
    if len(set(a))<2 or len(set(b))<2:return 0.0,True
    return float(np.corrcoef(rank(a),rank(b))[0,1]),False
def main():
    targets=rows(OLD/'data/temporal_fixed_validation.jsonl');assert len(targets)==89
    train=rows(OLD/'data/temporal_fixed_train.jsonl')
    train_scores=sorted(v for r in train for v in json.loads(r['messages'][1]['content'])['scores_x20'])
    cutoff=train_scores[math.ceil(.8*len(train_scores))-1]
    threshold_file=H/'selector_threshold.json'
    frozen={'threshold_x20':cutoff,'rule':'TRAIN_HUMAN_FIXED_GRID_NEAREST_RANK_80TH_PERCENTILE; scores>=threshold; empty allowed',
            'train_file_sha256':sha(OLD/'data/temporal_fixed_train.jsonl'),'fixed_bin_extension':'Entire label-independent 2-second ordinal domain; assumption not semantic boundary gold'}
    if threshold_file.exists():assert json.loads(threshold_file.read_text())==frozen
    else:
        with threshold_file.open('x') as f:json.dump(frozen,f,indent=2)
    arms={};ids={r['id'] for r in targets};gold_by_source=collections.defaultdict(list)
    for t in targets:
        values=json.loads(t['messages'][1]['content'])['scores_x20']
        for ordinal,g,value in zip(t['native_ordinals'],t['grid_indices'],values):gold_by_source[t['source_id']].append((ordinal,g,value))
    for source in gold_by_source:gold_by_source[source].sort()
    for name in ('new','base','pilot','production_B'):
        data=rows(H/'results'/f'{name}_predictions.jsonl');lookup={r['id']:r for r in data}
        assert len(data)==len(lookup)==89 and set(lookup)==ids
        source_values=collections.defaultdict(list)
        for t in targets:
            p=lookup[t['id']];answer=json.loads(p['answer'])
            assert set(answer)=={'scores_x20'} and len(answer['scores_x20'])==len(t['images']) and p['gold_in_input'] is False
            assert all(type(v) is int and 20<=v<=100 for v in answer['scores_x20'])
            for ordinal,g,pred,gold in zip(t['native_ordinals'],t['grid_indices'],answer['scores_x20'],json.loads(t['messages'][1]['content'])['scores_x20']):
                source_values[t['source_id']].append((ordinal,g,pred,gold))
        metrics={}
        for source,values in source_values.items():
            values.sort();n=len(values);assert n==len(gold_by_source[source]);pred=[v[2] for v in values];gold=[v[3] for v in values]
            corr,constant=rho(pred,gold);k=math.ceil(.15*n)
            indices=sorted(range(n),key=lambda i:(-pred[i],values[i][0]))[:k]
            selected=[v for v in values if v[2]>=cutoff]
            metrics[source]={'frames':n,'spearman':corr,'constant_ranking':constant,'top15_count':k,
              'top15_human_mean':sum(gold[i] for i in indices)/k/20,'mae':sum(abs(a-b) for a,b in zip(pred,gold))/n/20,
              'threshold_selected_fraction':len(selected)/n,'threshold_selected_human_mean':sum(v[3] for v in selected)/len(selected)/20 if selected else None,
              'threshold_low_human_fraction':sum(v[3]<60 for v in selected)/len(selected) if selected else None,
              'predictions':values}
        arms[name]={'rows':89,'all_outputs_valid':True,'source_metrics':metrics,
                    'macro_spearman':sum(v['spearman'] for v in metrics.values())/9,
                    'macro_top15_human_mean':sum(v['top15_human_mean'] for v in metrics.values())/9,
                    'production_B_scope':'Same adapter under new image-score prompt; NOT original B native-video pipeline comparison' if name=='production_B' else None}
    sources=sorted(gold_by_source);delta_rho=[arms['new']['source_metrics'][s]['spearman']-arms['base']['source_metrics'][s]['spearman'] for s in sources]
    delta_utility=[arms['new']['source_metrics'][s]['top15_human_mean']-arms['base']['source_metrics'][s]['top15_human_mean'] for s in sources]
    rng=np.random.default_rng(20261010);draw=rng.integers(0,9,size=(10000,9))
    bootstrap={name:np.quantile(np.asarray(v)[draw].mean(axis=1),[.025,.975]).tolist() for name,v in [('macro_spearman',delta_rho),('macro_top15_utility',delta_utility)]}
    gate=sum(delta_rho)/9>0 and sum(delta_utility)/9>0 and sum(v>0 for v in delta_rho)>=5
    vision=json.loads((H/'results/vision_dependency.json').read_text());gate=gate and vision['visual_dependency_gate']
    native_blocks=rows(OLD/'human_native_blocks.jsonl');grid=rows(OLD/'fixed_grid_samples.jsonl')
    bins={ (s['source_id'],s['grid_index']):s for s in grid if s['split']=='validation'}
    native={}
    for arm,values in arms.items():
        aggregate={}
        for source,m in values['source_metrics'].items():
            intervals=[(bins[(source,v[1])]['first_native_ordinal'],bins[(source,v[1])]['end_native_ordinal_exclusive']) for v in m['predictions'] if v[2]>=cutoff]
            blocks=[b for b in native_blocks if b['source_id']==source];total=sum(b['end_native_ordinal_exclusive']-b['first_native_ordinal'] for b in blocks)
            selected=gold_sum=low=0;high_total=high_selected=0
            for b in blocks:
                a,z=b['first_native_ordinal'],b['end_native_ordinal_exclusive'];human=b['worker_score_sum']/20
                count=sum(max(0,min(z,stop)-max(a,start)) for start,stop in intervals)
                assert 0<=count<=z-a
                selected+=count;gold_sum+=count*human;low+=count if human<3 else 0
                if human>=3:high_total+=z-a;high_selected+=count
            aggregate[source]={'native_frames':total,'selected_frames':selected,'selected_fraction':selected/total,
                'selected_human_mean':gold_sum/selected if selected else None,'selected_human_below3_fraction':low/selected if selected else None,
                'threshold3_human_proxy_precision':high_selected/selected if selected else 0,'threshold3_human_proxy_recall':high_selected/high_total if high_total else None,
                'threshold3_human_proxy_f':2*high_selected/(selected+high_total) if selected+high_total else 1,
                'AIC_score':False,'bin_expansion_is_assumption':True}
        native[arm]=aggregate
    report={'status':'PASS_FROZEN_RESEARCH_GATE' if gate else 'FAIL_FROZEN_RESEARCH_GATE_KEEP_PRODUCTION',
      'arms':arms,'source_deltas':dict(zip(sources,zip(delta_rho,delta_utility))),'source_bootstrap95':bootstrap,
      'worst_spearman_delta':min(delta_rho),'positive_sources':sum(x>0 for x in delta_rho),
      'visual_dependency':vision,'native_selector_analysis':native,'selector_threshold':frozen,
      'development_seen_before':True,'independent_AIC_quality_reference':None,'no_validation_based_recipe_retry':True}
    with (H/'quality_result.json').open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('arms','native_selector_analysis','visual_dependency')},indent=2))
if __name__=='__main__':main()
