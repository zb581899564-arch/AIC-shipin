"""Read-only actual failed teacher stream smoke. Never launches the teacher."""
import argparse
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'science_runtime'))
import science_contract as science


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--call-dir',default=str(HERE.parent/'teacher_calls/000'))
    args=parser.parse_args();folder=Path(args.call_dir).resolve(strict=True)
    stream=folder/'stdout.jsonl';terminal=folder/'terminal.json'
    receipt=json.loads(terminal.read_text(encoding='utf-8-sig'))
    assert science.sha(stream)==receipt['stdout_sha256'] and receipt['result_status']=='ERROR'
    rows=[json.loads(line) for line in stream.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    results=[r['result'] for r in rows if r.get('event')=='result']
    assert len(results)==1 and results[0]['status']=='ERROR'
    assert 'User location is not supported' in results[0]['error']
    done=[r['step_update'] for r in rows if r.get('event')=='step_update' and
          r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('tool_name')=='view_file' and
          r['step_update'].get('state')=='DONE']
    assert not done and receipt['usage']['total_tokens']==0
    # Do not manufacture sheet observations to match the unavailable teacher.
    audit=dict(original_stream=dict(path=str(stream),sha256=science.sha(stream)),sheet_observations=[])
    try:science.verify_teacher_stream(audit,[])
    except ValueError as exc:
        assert str(exc)=='teacher stream has real ERROR/failure'
    else:raise AssertionError('actual failed stream admitted')
    print(json.dumps(dict(status='PASS_ACTUAL_FAILED_TEACHER_STREAM_NEGATIVE_SMOKE_ONLY',
        stdout=dict(path=str(stream),sha256=science.sha(stream)),terminal=dict(path=str(terminal),sha256=science.sha(terminal)),
        actual_error=results[0]['error'],actual_successful_image_tools=0,actual_usage=receipt['usage'],
        teacher_cash=receipt['teacher_cash'],actual_terminal_exit_code=receipt['exit_code'],
        stream_acceptance=False,teacher_restarted=False,new_model_calls=0,new_native_decoder_calls=0,
        new_processor_calls=0,new_optimizer_updates=0)))


if __name__=='__main__':main()
