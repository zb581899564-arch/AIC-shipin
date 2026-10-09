"""Full new source field first, fixed V14 time projection second, independent strict."""
import argparse
from pathlib import Path

from sg8_common import HERE,V14,read,rows,sha,save,require,utc,inputs,old_helpers,verify
from sg8_field import compose
from sg8_independent_field import strict


def package(scope):
    verify(full=False)
    require(read(HERE/'diagnostic_01/report.json')['status']=='PASS_G2_NUMERIC_ONLY_G3_PENDING','G2 gate has not passed')
    if scope=='rematch':
        nt=read(HERE/'nontest_01/package.stage.json')
        require(nt['status']=='PASS_G3_NONTEST_NEW_FIELD_EFFECT_AND_STRICT' and nt['selected_integer_box_changes']>0,
            'NO_EFFECT cannot be rescued with 426')
    config,manifest,_=inputs(scope);common,_,_=old_helpers()
    import sys
    projected=sys.modules['frame_contract'].legacy_manifest(manifest)
    pc=sys.modules['package_contract']
    authority=V14/(scope+'_01');folder=HERE/(scope+'_01');folder.mkdir(exist_ok=False)
    selected=rows(authority/'selected.jsonl');fields=rows(authority/'field_frames.jsonl');shots=rows(authority/'field_shots.jsonl')
    requests=rows(authority/'anchor_requests.jsonl');outputs=rows(authority/'anchor_output.jsonl')
    full,full_prov,pred,prov=compose(projected,selected,fields,shots,requests,outputs)
    require(len(pred)==(8 if scope=='nontest' else 426),'complete source denominator')
    for name,value in [('full_field_predictions.jsonl',full),('full_field_provenance.jsonl',full_prov),
                       ('predictions.jsonl',pred),('provenance.jsonl',prov)]:
        pc.write_rows(folder/name,value)
    zip_path=folder/('NONTEST_ONLY_8_SG8.zip' if scope=='nontest' else 'candidate_SG8_PCHIP_8B.zip')
    pc.package(folder/'predictions.jsonl',zip_path)
    validation=strict(projected,selected,pred,prov,fields,shots,requests,outputs,folder/'predictions.jsonl',zip_path,full,full_prov)
    validation['utc']=utc();save(folder/'independent_validation.json',validation)
    old={(r['video_id'],p['frame']):p['bboxes'] for r in rows(authority/'predictions.jsonl') for p in r['predictions']}
    new={(r['video_id'],p['frame']):p['bboxes'] for r in pred for p in r['predictions']}
    require(set(new)==set(old) and len(new)==(447 if scope=='nontest' else 102470),'fixed complete V14 time keys changed')
    changes=sum(new[k]!=old[k] for k in new)
    stage=dict(status=('PASS_G3_NONTEST_NEW_FIELD_EFFECT_AND_STRICT' if changes else 'NO_EFFECT') if scope=='nontest'
        else 'PASS_FULL_426_NEW_SPATIAL_FIELD_AND_STRICT',utc=utc(),scope=scope,video_records=len(pred),
        selected_frames=len(new),selected_integer_box_changes=changes,full_source_frames=len(full_prov),
        original_anchor_count=len(outputs),original_time_sha256=sha(authority/'temporal.jsonl'),
        original_anchor_output_sha256=sha(authority/'anchor_output.jsonl'),
        actual_new_space_model_calls=0,actual_new_time_model_calls=0,new_optimizer_updates=0,
        candidate=dict(path=str(zip_path),bytes=zip_path.stat().st_size,sha256=sha(zip_path)),
        files={name:sha(folder/name) for name in ['full_field_predictions.jsonl','full_field_provenance.jsonl',
            'predictions.jsonl','provenance.jsonl','independent_validation.json']},
        original_space_cost_seconds_preserved=18723.876,official_score=None,uploaded=False)
    save(folder/'package.stage.json',stage)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('scope',choices=['nontest','rematch']);package(p.parse_args().scope)
