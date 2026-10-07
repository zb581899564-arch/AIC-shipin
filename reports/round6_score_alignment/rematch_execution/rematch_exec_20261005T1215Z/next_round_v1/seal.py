"""Byte-bind new sources, fixed existing model and input identities before launch."""
from common import *
import datetime as dt

def main():
    require(not (HERE/'source_lock.json').exists(),'never reseal registered execution')
    config=read(HERE/'config.json');files={}
    require(read(HERE/'cpu_02/processor_acceptance.json')['status']=='PASS_REAL_PROCESSOR_AND_EMPTY_TARGET','missing processor evidence')
    files[str(HERE/'cpu_02/processor_acceptance.json')]=sha(HERE/'cpu_02/processor_acceptance.json')
    for suffix in ('*.py','*.md','*.json','*.ps1','*.txt'):
        for path in HERE.glob(suffix):
            if path.name=='source_lock.json':continue
            files[str(path)]=sha(path)
    for path in (HERE/'supervision').glob('*'):
        if path.is_file():files[str(path)]=sha(path)
    dependencies=list(BASELINE.rglob('*.py'))+[RUN/'temporal_sft8b_v1'/n for n in ('train_sft.py','sft_contract.py')]
    dependencies += [RUN/'temporal_sft8b_dev_v1/evaluate.py',Path(config['open_dev_contract'])]
    r7=ROOT/'round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z'
    dependencies += [r7/'code'/n for n in ('temporal_common.py','r7_core.py')]
    dependencies += [r7/'inputs'/n for n in ('train_temporal.jsonl','dev_temporal.jsonl','split_freeze.json')]
    for value in config['inputs'].values():
        for key in ('manifest','registry'):
            require(sha(value[key])==value[key+'_sha256'],'registered input changed')
            dependencies.append(Path(value[key]))
    receipt=Path(config['model_receipt']['path'])
    require(sha(receipt)==config['model_receipt']['sha256'],'model receipt changed')
    dependencies.append(receipt)
    for item in read(receipt)['completed']:
        path=Path(config['model_dir'])/item['name']
        require(sha(path)==item['sha256'],'fixed model byte changed')
        dependencies.append(path)
    adapter=Path(config['b_adapter'])
    require(sha(adapter/'adapter_model.safetensors')==config['b_adapter_sha256'],'final B adapter changed')
    dependencies += [adapter/'adapter_config.json',adapter/'adapter_model.safetensors']
    for path in dependencies:files[str(path)]=sha(path)
    write(HERE/'source_lock.json',dict(schema='NEXT8B_V1_SOURCE_LOCK',frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files=files,
        old_runtime_files_modified=False,gpu_time_cumulative_unlimited=True,ledger_initial_offset_seconds=7200))
    print(json.dumps(dict(status='PASS_BYTE_BINDING',files=len(files),source_lock_sha256=sha(HERE/'source_lock.json'))),flush=True)

if __name__=='__main__':main()
