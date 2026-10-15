"""First media -> native CPU -> same-B -> first QA -> fresh confirmation.

This controller never starts fixed40, production, packaging, or old recovery.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback
import model_common as io


def main(root):
    io.host(cpu=False)
    root=io.root_path(root)
    gate=io.fresh_gate(root,'confirm')
    state=root/'fresh_control_01';state.mkdir(exist_ok=False)
    io.require(not (root/'confirm').exists(),'A started media/confirm stage must not be repeated')
    io.save(state/'started.json',dict(utc=io.utc(),pid=os.getpid(),parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],
        protocol_sha256=gate['protocol_sha256'],registration_sha256=gate['registration_sha256'],
        original_calls_repeated=False,production_admitted=False))
    stage='FIRST_FRESH_MEDIA_NATIVE_REFERENCE'
    try:
        argv=[sys.executable,'-B','-u',str(root/'code/prepare_fresh_reference.py'),'--root',str(root)]
        with (state/'media.log').open('xb') as log:
            p=subprocess.run(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdout=log,stderr=subprocess.STDOUT)
        io.require(p.returncode==0,'Actual first media/native failure; preserve all success, no automatic retry')
        stage='FIRST_FRESH_INPUTS_MODELS_QA_CONFIRMATION'
        argv=[sys.executable,'-B','-u',str(root/'code/pilot_chain_fresh.py'),'--root',str(root),'--group','confirm']
        with (state/'chain.log').open('xb') as log:
            p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
        io.require(p.returncode==0,'Actual independent chain failed; preserve stage failure/raw/fees, never restart success')
        path=root/'confirm/chain_01/completion.json';value=io.read(path)
        io.require(value['status'] in ('PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40','STOP_CONSENSUS_FRESH_CONFIRM_REJECTED'),
                   'Actual unique scientific terminal required')
        io.save(state/'completion.json',dict(utc=io.utc(),status=value['status'],chain_completion_ref=dict(path=str(path),sha256=io.sha(path)),
            production_admitted=False,no_fixed40_426_or_package_started=True))
    except BaseException as error:
        io.save(state/'failure.json',dict(utc=io.utc(),stage=stage,error=repr(error),traceback=traceback.format_exc(),
            preserve_all_success=True,no_automatic_restart=True,production_admitted=False))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();main(a.root)
