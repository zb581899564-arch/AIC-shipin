"""Prove STOP refuses before any ML/decoder framework import on Linux."""
import contextlib
import hashlib
import importlib.abc
import io
import json
from pathlib import Path
import runpy
import sys

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
BLOCKED={'torch','numpy','transformers','peft','decord','av'}
attempted=[]
class FrameworkGuard(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path,target=None):
        if fullname.split('.')[0] in BLOCKED:
            attempted.append(fullname)
            raise RuntimeError('STOP verification attempted framework import: '+fullname)
        return None
if __name__=='__main__':
    dense=RUN/'dense_head'
    sys.path.insert(0,str(dense))
    sys.meta_path.insert(0,FrameworkGuard())
    sys.argv=[str(dense/'train_dense.py'),'--admission',str(dense/'formal_admission_TEMPLATE_DO_NOT_RUN.json'),
              '--config',str(dense/'formal_config_TEMPLATE_DO_NOT_RUN.json'),'--admission-check-only']
    output=io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            runpy.run_path(str(dense/'train_dense.py'),run_name='__main__')
            code=0
        except SystemExit as exc:
            code=exc.code
    actual=json.loads(output.getvalue())
    passed=(code==1 and actual['status']=='REJECTED_FORMAL_ADMISSION_OR_CONTRACT'
            and actual['started_runtime'] is False and not attempted
            and not any(name.split('.')[0] in BLOCKED for name in sys.modules))
    report={'status':'PASS_CURRENT_STOP_BEFORE_RUNTIME' if passed else 'FAIL_STOP_VERIFICATION',
            'expected_exit_code':1,'actual_exit_code':code,'actual_cli_report':actual,
            'framework_import_attempts':attempted,'frameworks_imported':False,
            'training_source_sha256':hashlib.sha256((dense/'train_dense.py').read_bytes()).hexdigest(),
            'gpu_used':False,'models_run':False,'media_decoded':False}
    with (RUN/'controller/formal_stop_linux_receipt.json').open('x') as handle:
        json.dump(report,handle,indent=2)
        handle.write('\n')
    print(json.dumps(report),flush=True)
    raise SystemExit(0 if passed else 1)
