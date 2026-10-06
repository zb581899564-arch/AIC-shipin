from runtime import *
old=RUN/'b_sft8b_package_v2/rematch_01/temporal.jsonl'
require(read(RUN/'b_sft8b_package_v2/completion.json')['stage']=='STOP_B8B_PACKAGE_CONTINUATION','old stopped run not reconciled')
old_rows=rows(old);require(old_rows and len({r['video_id'] for r in old_rows})==len(old_rows),'partial source identity invalid')
accepted=failed=0
for r in old_rows:
    for w in r['windows']:
        if w.get('output_valid') is True:
            require(w['status']=='MODEL_OK' and not w['parse_errors'],'successful window invalid');accepted+=1
        else:
            require(w['status']=='INFERENCE_FAILURE' and w['parse_errors']==['RuntimeError: expanded temporal sequence exceeds training contract'],
                'non-guard failure cannot enter this recovery');failed+=1
write(HERE/'partial_recovery_inputs.json',dict(partial_path=str(old),partial_sha256=sha(old),videos=len(old_rows),
    successful_windows_to_keep=accepted,pre_generation_guard_failures=failed,old_output_unchanged=True,
    no_raw_outputs_displayed=True,failed_run_kept=True,training_limit_unchanged=8192,inference_limit=16384))
print(json.dumps(dict(status='PASS_PRE_GENERATION_RECOVERY_BINDING',videos=len(old_rows),successful_windows_to_keep=accepted,pre_generation_guard_failures=failed,partial_sha256=sha(old))))
