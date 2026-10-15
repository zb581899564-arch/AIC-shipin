"""Future metadata-only HALF closure. Never creates package admission or ZIP."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import sys

from half_bind_contract import (SCHEMA,PARAMETERS,HALF_PROTOCOL_SHA,HALF_RENDERER_SHA,
    ORIGINAL_RENDERER_SHA,digest,valid_sha,require,original_count,production_gate,
    protocol_gate,lock_union,merge_history)

HOME=Path('/home/inspur/aic_video_work')
CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
BASE=CAMPAIGN/'temporal_family_half_bootstrap_control7_v1'
ROOT=CAMPAIGN/'temporal_family_half_package_v1'
ORIGINAL=CAMPAIGN/'temporal_family_native_package_v3'
CONTROL=CAMPAIGN/'temporal_global_recovery_control7_v1'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())


class MetadataClosure:
    def __init__(self):self.files={};self.deferred={}
    def path(self,ref):
        require(isinstance(ref,dict) and valid_sha(ref.get('sha256')),'Frozen actual metadata SHA required')
        path=Path(ref['path']).absolute()
        require(str(path).startswith('/') and '..' not in path.parts and path.is_relative_to(HOME) and
            all(not part.is_symlink() for part in (path,*path.parents)) and path.is_file(),
            'Closure escaped Linux HOME or followed a link')
        require('bytes' not in ref or path.stat().st_size==ref['bytes'],'Immutable artifact byte count changed')
        return path
    def add(self,ref,read_body=False):
        path=self.path(ref);key=str(path)
        require(key not in self.files or self.files[key]==ref['sha256'],'Conflicting immutable source SHA')
        if read_body:
            require(path.suffix in ('.json','.py','.md'),'Only technical JSON/code bodies may be read')
            require(sha(path)==ref['sha256'],'Technical metadata or code changed')
        else:
            self.deferred[key]=dict(sha256=ref['sha256'],bytes=path.stat().st_size,
                digest_source='ORIGINAL_NATURALLY_COMPLETED_PACKAGE_ACCEPTED_LOCK',final_renderer_checks_file_SHA=True)
        self.files[key]=ref['sha256'];return path
    def load(self,ref):
        path=self.add(ref,read_body=True);require(path.suffix=='.json','Technical JSON only')
        return json.loads(path.read_text(encoding='utf-8-sig'))
    def inherit(self,old):
        for path,checksum in old['files'].items():self.add(dict(path=path,sha256=checksum))
        self.files=lock_union(old['files'],self.files)
    def copy(self,ref,target):
        source=self.add(ref,read_body=True)
        require(source.suffix=='.json' and target.parent==ROOT,'Only HALF root technical document copies')
        if target.exists():require(sha(target)==ref['sha256'],'Existing HALF document differs; retain it')
        else:
            with source.open('rb') as src,target.open('xb') as dst:
                for chunk in iter(lambda:src.read(1<<20),b''):dst.write(chunk)
                dst.flush();os.fsync(dst.fileno())
        return self.add(dict(path=str(target),sha256=ref['sha256']),read_body=True)


def natural_family(closure,config,family_ref):
    value=closure.load(config['original_family_natural_terminal_ref'])
    require(value['status']=='PASS_ORIGINAL_EIGHT_ARM_RENDERER_NATURAL_EXIT0' and
        type(value['exit_code'])is int and value['exit_code']==0 and value['naturally_completed'] is True and
        value['completion_ref']==family_ref and
        value['renderer_ref']==dict(path=str(ORIGINAL/'code/package_family.py'),sha256=ORIGINAL_RENDERER_SHA) and
        value['process_was_killed_or_restarted'] is False,
        'Original family completion file alone is not its actual natural process terminal')
    require(str(ORIGINAL/'code/package_family.py') in value['argv'],'Natural family terminal argv does not name its frozen renderer')
    closure.add(value['renderer_ref'],read_body=True)


def bind(config_path):
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5' and
        os.environ.get('CUDA_VISIBLE_DEVICES')=='','Linux metadata CPU child only')
    require(Path(__file__).resolve().parent==BASE/'code','Independent fixed HALF bootstrap owner required')
    config_path=Path(config_path).absolute();require(config_path.is_relative_to(BASE),'New frozen HALF bootstrap config root')
    config=json.loads(config_path.read_text());closure=MetadataClosure()
    require(config['schema']==SCHEMA and config['metadata_binding_approved_by_main'] is True and
        config['package_root']==str(ROOT) and config['create_package_admission'] is False and
        config['test_GT_or_manual_test_content_read'] is False,'No separate technical binding approval')
    family_ref=config['original_family_completion_ref']
    require(Path(family_ref['path']).absolute()==ORIGINAL/'completion.json','Actual fixed original family completion only')
    family=closure.load(family_ref);count=original_count(family);natural_family(closure,config,family_ref)
    require(not (ORIGINAL/'failure.json').exists(),'A failed original family cannot be supplemented automatically')
    if count>=5:
        result=dict(status='SKIP_HALF_ORIGINAL_FIVE_SUFFICIENT_NO_HALF_WRITES',original_actual_packages=count,
            metadata_files_created=0,package_admission_created=False,new_ZIPs=0)
        print(json.dumps(result));return result
    # All checks before new target writes; partial technical writes are kept and
    # never silently overwritten/retried. Existing complete HALF work blocks.
    require(ROOT.is_dir() and not (ROOT/'package_admission.json').exists() and
        not (ROOT/'started.json').exists() and not (ROOT/'completion.json').exists() and not (ROOT/'failure.json').exists(),
        'HALF already admitted/attempted/completed; no repeat')
    names=('package_inputs.json','history.json','source_package_lock.json','technical_preparation_receipt.json')
    require(all(not (ROOT/name).exists() for name in names),'HALF technical binding already attempted; preserve partial success')
    require(Path(config['production_completion_ref']['path']).absolute()==CONTROL/'exports_01/global_completion.json' and
        Path(config['controller_completion_ref']['path']).absolute()==CONTROL/'run_01/completion.json','Actual CONTROL7 independent aggregate recovery terminals only')
    production=closure.load(config['production_completion_ref']);controller=closure.load(config['controller_completion_ref'])
    require(Path(config['original_technical_receipt_ref']['path']).absolute()==ORIGINAL/'technical_preparation_receipt.json' and
        Path(config['original_inputs_ref']['path']).absolute()==ORIGINAL/'package_inputs.json' and
        Path(config['original_source_lock_ref']['path']).absolute()==ORIGINAL/'source_package_lock.json',
        'Original successful package technical inputs/lock only')
    technical=closure.load(config['original_technical_receipt_ref']);inputs=closure.load(config['original_inputs_ref'])
    old_lock=closure.load(config['original_source_lock_ref'])
    production_gate(production,controller,technical,config['production_completion_ref'])
    require(technical['package_inputs_ref']==config['original_inputs_ref'] and
        technical['controller_completion_ref']==config['controller_completion_ref'] and
        inputs['production_completion']==config['production_completion_ref'] and
        inputs['development_selection']==production['frozen_development_selection_ref'] and
        all(inputs[name]==production['accepted_export_refs'][name] for name in ('events','endpoints','verification','source_clocks')),
        'Actual original accepted package projection differs from CONTROL7 recovery')
    require(old_lock['package_admission_created'] is False and old_lock['old_successes_reexecuted'] is False,
        'Original technical lock semantics changed')
    # Metadata files above must already belong to the actual accepted original
    # closure, except its own lock and the later original natural completion.
    for ref in (config['original_inputs_ref'],config['original_technical_receipt_ref'],config['production_completion_ref'],config['controller_completion_ref']):
        require(old_lock['files'].get(ref['path'])==ref['sha256'],'Original full source lock omitted accepted technical evidence')
    for path,checksum in config['required_binder_code_files'].items():closure.add(dict(path=path,sha256=checksum),read_body=True)
    require(set(config['required_binder_code_files'])=={str(p.absolute()) for p in (BASE/'code').glob('*.py')},
        'All actual new binding code must be frozen')
    code=config['half_package_code_refs']
    require(set(code)=={p.name for p in (ROOT/'code').glob('*.py')} and
        code['package_half.py']['sha256']==HALF_RENDERER_SHA,'Unchanged complete HALF renderer code required')
    for name,ref in code.items():
        require(Path(ref['path']).absolute()==ROOT/'code'/name,'HALF code owner escaped');closure.add(ref,read_body=True)
    require(old_lock['files'].get(str(ORIGINAL/'code/package_family.py'))==ORIGINAL_RENDERER_SHA,
        'Original actual renderer/code identity is not in the retained closure')
    supplied=config['package_document_refs'];require(set(supplied)=={'protocol','authorization','official_rule_check'},
        'New root-owned HALF protocol/risk/current-rule leaves required')
    require(supplied['protocol']['sha256']==HALF_PROTOCOL_SHA,'Fixed original HALF protocol bytes changed')
    protocol_gate(closure.load(supplied['protocol']))
    closure.load(supplied['authorization']);closure.load(supplied['official_rule_check'])
    history_ref=inputs['history'];require(old_lock['files'].get(history_ref['path'])==history_ref['sha256'],'Original frozen history was not locked')
    old_history=closure.load(history_ref);family_history=[]
    for row in family['packages']:
        out=ORIGINAL/('package_'+row['arm']);receipt_ref=dict(path=str(out/'completion.json'),sha256='')
        # Current natural family metadata names the actual ZIP/member/canonical
        # identities. Read only its small immutable receipt/11-strict report.
        receipt_path=out/'completion.json';receipt_ref['sha256']=sha(receipt_path)
        require(closure.load(receipt_ref)==row,'Natural family receipt differs from its actually completed package')
        require(row['source_package_lock_sha256']==config['original_source_lock_ref']['sha256'] and
            row['actual_production_completion_sha256']==config['production_completion_ref']['sha256'],
            'Actual original package has a different source/production closure')
        validation_ref=dict(path=str(out/'independent_validation.json'),sha256=row['independent_validation_sha256'])
        validation=closure.load(validation_ref)
        require(len(validation['checks'])==11 and all(validation['checks'].values()) and
            validation['prediction_frames']==row['frame_count'],'Actual original independent11 receipt incomplete')
        require(Path(row['zip']).absolute()==out/('candidate_TEMPORAL_'+row['arm']+'.zip'),'Original actual ZIP owner/name changed')
        closure.add(dict(path=row['zip'],sha256=row['SHA256'],bytes=row['bytes']))
        closure.add(dict(path=str(out/'predictions.jsonl'),sha256=row['member_SHA256']))
        family_history.append(dict(filename=Path(row['zip']).name,ZIP_SHA256=row['SHA256'],member_SHA256=row['member_SHA256'],
            canonical_SHA256=row['canonical_SHA256'],source_receipt_ref=receipt_ref,original_record_sha256=digest(row),
            original_family_completion_ref=family_ref))
    closure.inherit(old_lock)
    # The inherited lock is complete; no new media/RGB/tensor/raw/export/field
    # body is read or canonicalized. The fixed renderer rechecks retained SHA.
    merged=merge_history(old_history,family_history)
    config_ref=dict(path=str(config_path),sha256=sha(config_path));closure.add(config_ref,read_body=True)
    for name,ref in supplied.items():closure.copy(ref,ROOT/(name+'.json'))
    save(ROOT/'history.json',merged);new_history_ref=dict(path=str(ROOT/'history.json'),sha256=sha(ROOT/'history.json'))
    closure.add(new_history_ref,read_body=True)
    half_inputs=dict(inputs,history=new_history_ref,original_family_completion=family_ref)
    save(ROOT/'package_inputs.json',half_inputs);inputs_ref=dict(path=str(ROOT/'package_inputs.json'),sha256=sha(ROOT/'package_inputs.json'))
    closure.add(inputs_ref,read_body=True)
    receipt=dict(status='TECHNICAL_HALF_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM',finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        config_ref=config_ref,production_completion_ref=config['production_completion_ref'],controller_completion_ref=config['controller_completion_ref'],
        original_family_completion_ref=family_ref,original_family_natural_terminal_ref=config['original_family_natural_terminal_ref'],
        original_source_package_lock_ref=config['original_source_lock_ref'],original_history_ref=history_ref,history_ref=new_history_ref,
        package_inputs_ref=inputs_ref,original_actual_packages=count,remaining_publication_slots=5-count,
        maximum_new_HALF_packages=min(3,5-count),publication_priority=['HALF_START','HALF_END','HALF_BOTH'],
        source_count=426,event_count=665,endpoint_results=1330,verification_results=665,actual_MODEL_proofs=1992,
        full_original_lock_entries_carried=len(old_lock['files']),original_published_canonical_rows_added=len(family_history),
        physical_model_parameters=PARAMETERS,package_admission_created=False,final_main_rule_risk_veto_admission_required=True,
        scientific_quality_claim=False,old_successes_or_failed_gates_modified=False,old_family_rerun=False,
        formal_raw_export_tensor_field_ZIP_body_reads=0,media_decodes=0,processor_calls=0,model_calls=0,package_calls=0,new_ZIPs=0)
    save(ROOT/'technical_preparation_receipt.json',receipt)
    closure.add(dict(path=str(ROOT/'technical_preparation_receipt.json'),sha256=sha(ROOT/'technical_preparation_receipt.json')),read_body=True)
    save(ROOT/'source_package_lock.json',dict(schema='TEMPORAL_HALF_PACKAGE_COMPLETE_EXISTING_EVIDENCE_LOCK_V1',files=closure.files,
        original_full_source_package_lock_ref=config['original_source_lock_ref'],
        existing_accepted_payload_digests_deferred_to_renderer=closure.deferred,
        released_RGB_historical_refs=old_lock.get('released_RGB_historical_refs',[]),
        provenance_only_not_active_file_refs=old_lock.get('provenance_only_not_active_file_refs',[]),
        package_admission_created=False,old_successes_reexecuted=False,original_actual_packages=count,remaining_publication_slots=5-count))
    result=dict(status=receipt['status'],package_root=str(ROOT),source_package_lock_sha256=sha(ROOT/'source_package_lock.json'),
        remaining_publication_slots=5-count,package_admission_created=False,new_ZIPs=0)
    print(json.dumps(result));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';bind(args.config)
