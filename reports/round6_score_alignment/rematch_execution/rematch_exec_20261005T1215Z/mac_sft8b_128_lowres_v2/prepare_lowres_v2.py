"""One-time, explicit new recipe fork; the failed v1 remains byte-unchanged."""
import datetime as dt
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ASSET='/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z'
PROJECT='/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_128_lowres_20261006T0707Z'
SCOPE='MAC_8B_128_LOWRES_INTERVAL_SFT_NONTEST'
def change(name,old,new,count=1):
    path=HERE/name;source=path.read_text(encoding='utf-8')
    assert source.count(old)==count,(name,old,source.count(old))
    path.write_text(source.replace(old,new),encoding='utf-8')

config=json.loads((HERE/'config.json').read_text())
config.update(max_pixels=32768,max_sequence_length=6144,
    direction='128_FRAME_TEMPORAL_DENSITY_WITH_LOWER_SPATIAL_RESOLUTION',
    asset_root=ASSET,model_dir=ASSET+'/models/Qwen3-VL-8B-Instruct',
    python=ASSET+'/env/bin/python',probe_max_seconds=10800,
    planned_output_bytes=15335424*4+3620*6144*32+134217728,
    parent_failed_run=ASSET,scientific_change='Only pixel budget 131072->32768 and sequence ceiling 16384->6144; 128 sampled source ordinals and all SFT optimization/data settings retained')
(HERE/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
authority=dict(authorized=True,scope=SCOPE,
    user_request_quote='去修复内存问题，如果mac支撑不起128帧，那你就换个微调方向',
    authority_kind='USER_MEMORY_REPAIR_AND_DIFFERENT_MAC_DIRECTION_AUTHORIZATION',
    formal_C_BCE_admitted=False,prepare_and_bounded_probe_admitted=True,
    full_training_only_after_real_probe_pass=True,test_inference_admitted=False,official_upload_admitted=False,
    unique_root=PROJECT,parent_failed_run=ASSET,original_failed_evidence_preserved=True,
    logical_parameter_limit=9000000000,combined_host_peak_disk_limit_bytes=80*2**30,
    no_mps_limit_disable=True,no_implicit_cpu_fallback=True,registered_utc=dt.datetime.now(dt.timezone.utc).isoformat())
(HERE/'authorization.json').write_text(json.dumps(authority,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
change('mac_contract.py',"SCOPE='MAC_8B_128_FRAME_INTERVAL_SFT_NONTEST'",f"SCOPE='{SCOPE}'\nASSET_ROOT=Path('{ASSET}')")
change('mac_contract.py',"authority['user_request_quote']=='mac微调模型不应该更有优势？mac再去微调一个版本怎么样'",
       "authority['user_request_quote']=='去修复内存问题，如果mac支撑不起128帧，那你就换个微调方向'")
change('mac_contract.py',"config['max_pixels']==131072 and config['max_sequence_length']==16384",
       "config['max_pixels']==32768 and config['max_sequence_length']==6144")
change('mac_contract.py',"asset_path=HERE/'controller/asset_http_completion.json'","asset_path=ASSET_ROOT/'controller/asset_http_completion.json'")
change('mac_contract.py',"asset_path=HERE/'controller/asset_completion.json'","asset_path=ASSET_ROOT/'controller/asset_completion.json'")
change('mac_contract.py',"(HERE/'controller/environment_completion.json')","(ASSET_ROOT/'controller/environment_completion.json')")
change('mac_contract.py',"verify_model_receipt(HERE/'models/Qwen3-VL-8B-Instruct'","verify_model_receipt(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct'")
change('mac_contract.py',"model_dir=str(HERE/'models/Qwen3-VL-8B-Instruct')","model_dir=str(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct')")
change('mac_inputs.py','MAX_FRAMES=128,MAX_PIXELS=131072','MAX_FRAMES=128,MAX_PIXELS=32768')
change('train_mac.py','tc.MAX_PIXELS==131072','tc.MAX_PIXELS==32768')
change('train_mac.py','min_pixels=131072,max_pixels=131072','min_pixels=32768,max_pixels=32768')
change('test_mac_cpu.py','from mac_contract import epoch_batches,HERE','from mac_contract import epoch_batches,HERE,ASSET_ROOT')
change('test_mac_cpu.py',"str(HERE/'models/Qwen3-VL-8B-Instruct')","str(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct')")
change('test_mac_cpu.py','min_pixels=131072,max_pixels=131072','min_pixels=32768,max_pixels=32768')
change('test_mac_cpu.py',"dict(max_sequence_length=16384)","dict(max_sequence_length=6144)")
change('test_mac_cpu.py',"self.assertLessEqual(encoded['input_ids'].shape[1],16384)","self.assertLessEqual(encoded['input_ids'].shape[1],6144)")
change('record_preflight.py',"HERE=Path(__file__).resolve().parent;ROOT=Path('/Users/choubk/codex-workspace')",
       f"HERE=Path(__file__).resolve().parent;ROOT=Path('/Users/choubk/codex-workspace');ASSET_ROOT=Path('{ASSET}')")
change('record_preflight.py',"Path(sys.executable)==HERE/'env/bin/python'","Path(sys.executable)==ASSET_ROOT/'env/bin/python'")
change('finish_mac.py','from mac_contract import HERE,ROOT,SCOPE,verify_lock','from mac_contract import HERE,ROOT,SCOPE,ASSET_ROOT,verify_lock')
change('finish_mac.py',"HERE/'env/bin/python'","ASSET_ROOT/'env/bin/python'",2)
change('finish_mac.py',"asset=CTRL/'asset_http_completion.json'","asset=ASSET_ROOT/'controller/asset_http_completion.json'")
change('finish_mac.py',"(CTRL/'environment_completion.json')","(ASSET_ROOT/'controller/environment_completion.json')")
change('finish_mac.py','48*16384*32','48*6144*32')
change('launch_owned_mac.py',"str(HERE/'env/bin/python')",f"'{ASSET}/env/bin/python'")
change('status_mac.py',"transfer=read(CTRL/'asset_http_completion.json') or read(CTRL/'asset_http_progress.json')",
       f"asset_ctrl=Path('{ASSET}')/'controller'\ntransfer=read(asset_ctrl/'asset_http_completion.json') or read(asset_ctrl/'asset_http_progress.json')")
print(json.dumps(dict(status='PREPARED_NEW_EXPLICIT_128_LOWRES_RECIPE',project=PROJECT,pixels=32768,max_sequence=6144)))
