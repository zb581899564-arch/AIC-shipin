"""CPU child invokes precisely one input-layer first replay; no output/model call."""
import argparse
import os
from pathlib import Path

import pc_io as io


def main(registration_path,consumer,batch_id):
    io.host();ctx=io.load(registration_path)
    batch=next(batch for batch in ctx['batches'] if batch['batch_id']==batch_id)
    from pc_contract import require
    require(consumer in batch['request_ids'],'Unfrozen first replay consumer')
    module=io.module('_pc_first_input_replay',io.INPUT/'code/replay_input.py')
    pointer=io.read(io.RUNTIME/'runs'/batch_id/'terminal_pointer.json')
    module.first_input_replay(ctx['lib']['input_reg'],consumer,pointer['resource_ref'],pointer['ledger_ref'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path);parser.add_argument('--consumer',required=True)
    parser.add_argument('--batch-id',required=True);args=parser.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';main(args.registration,args.consumer,args.batch_id)
