"""Independent closure: accepted raw receipts, exact gate, full field and ledger."""
from pathlib import Path
import sys
from sg8_common import HERE,RUN,V14,read,rows,sha,digest,save,require,utc,verify,inputs,old_helpers
from sg8_report import reconstruct
from sg8_independent_field import strict


def terminal():
    path=RUN/'controller/aic_SG8_slot4_v2_diagnostic.resource.json';v=read(path)
    ledger=rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    admission=read(HERE/'g0_admission.json');n=admission['ledger_prefix_records']
    require(digest(ledger[:n])==admission['ledger_prefix_digest'] and ledger[0]['prior_charged_seconds']==7200,
        'historical ledger prefix/offset changed')
    require(v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0 and
        sum(r['name']==v['name'] for r in ledger)==1 and sum(r==v for r in ledger)==1,'actual GPU unique natural terminal is missing')
    return dict(path=str(path),sha256=sha(path),charged_seconds=v['charged_seconds'],
        sampled_peak_memory_mib=v['sampled_peak_memory_mib'],unique_terminal_ledger_match=True,ledger_records=len(ledger))


def main():
    verify();resource=terminal()
    expected=reconstruct();stored=read(HERE/'diagnostic_01/report.json');stored.pop('utc')
    require(expected==stored and expected['status']=='PASS_G2_NUMERIC_ONLY_G3_PENDING','independent numeric gate reconstruction differs')
    validation={}
    for scope in ['nontest','rematch']:
        _,manifest,_=inputs(scope);old_helpers();manifest=sys.modules['frame_contract'].legacy_manifest(manifest)
        authority=V14/(scope+'_01');folder=HERE/(scope+'_01');stage=read(folder/'package.stage.json')
        for name,expected_sha in stage['files'].items():require(sha(folder/name)==expected_sha,'new full field/package bytes changed')
        candidate=stage['candidate'];require(sha(candidate['path'])==candidate['sha256'] and Path(candidate['path']).stat().st_size==candidate['bytes'],
            'actual candidate size/SHA differs')
        value=strict(manifest,rows(authority/'selected.jsonl'),rows(folder/'predictions.jsonl'),rows(folder/'provenance.jsonl'),
            rows(authority/'field_frames.jsonl'),rows(authority/'field_shots.jsonl'),rows(authority/'anchor_requests.jsonl'),
            rows(authority/'anchor_output.jsonl'),folder/'predictions.jsonl',candidate['path'],
            rows(folder/'full_field_predictions.jsonl'),rows(folder/'full_field_provenance.jsonl'))
        require(value=={k:v for k,v in read(folder/'independent_validation.json').items() if k!='utc'},'independent whole-field strict reconstruction differs')
        require(stage['selected_integer_box_changes']>0 if scope=='nontest' else True,'NONTEST NO_EFFECT')
        validation[scope]=dict(video_records=value['video_records'],selected_frames=value['selected_frames'],
            full_source_frames=value['counts']['full_source_frames'],original_anchors=value['counts']['original_anchors'],
            checks=value['checks'],new_math_and_four_support_exact=True,selected_integer_box_changes=stage['selected_integer_box_changes'])
    require(validation['rematch']['selected_frames']==102470 and validation['rematch']['original_anchors']==31295 and
        validation['rematch']['video_records']==426,'complete final denominator differs')
    save(HERE/'final_acceptance.json',dict(status='PASS_INDEPENDENT_SG8_PCHIP_FINAL',utc=utc(),
        candidate=read(HERE/'rematch_01/package.stage.json')['candidate'],scopes=validation,resource=resource,
        source_lock_sha256=sha(HERE/'source_lock.json'),numeric_report_sha256=sha(HERE/'diagnostic_01/report.json'),
        actual_new_space_calls=53,exact_old_probe_references=3,new_426_model_calls=0,new_time_calls=0,
        new_optimizer_updates=0,production_temporal_adapter='ORIGINAL_B_EPOCH0',space_adapter_enabled=False,
        space_parameters=8767123696,logical_pipeline_parameters=8782459120,
        original_space_cost_seconds_preserved=18723.876,official_score=None,composition_truth='UNKNOWN',
        decoder_replays_repeated=0,automatically_returned=False,uploaded=False))


if __name__=='__main__':main()
