"""Unique original-media stage; authorization and checksum-bound inputs are mandatory."""
import argparse, datetime, hashlib, json, socket, traceback
from pathlib import Path
from download_sources_remote import main, OUT, save
BASE=Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    assert socket.gethostname()=='inspur-NP5570M5'
    registration_path=BASE/'human_source_registration_01.json'
    registration=json.loads(registration_path.read_text(encoding='utf-8-sig'))
    authorization=json.loads((BASE/'media_download_authorization_01.json').read_text(encoding='utf-8-sig'))
    assert hashlib.sha256(registration_path.read_bytes()).hexdigest()==authorization['registration_sha256']
    try:
        if args.resume: assert not (OUT/'completion.json').exists(), 'Completed download cannot be restarted'
        main(registration,authorization,resume=args.resume)
    except BaseException as error:
        if OUT.exists() and not (OUT/'failure.json').exists():
            save(OUT/'failure.json',dict(status='FAILED_MEDIA_STAGE_PRESERVE_SUCCESS_AND_PARTIAL',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exception=repr(error),traceback=traceback.format_exc(),new_model_calls=0))
        raise
