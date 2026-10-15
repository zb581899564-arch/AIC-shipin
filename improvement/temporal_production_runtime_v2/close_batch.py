"""Close all batch consumers first, then release only their predeclared new RGB."""
import argparse
import os
from pathlib import Path

import pr_contract as c
import pr_io as io


def close(protocol_path,batch_id):
    io.host(cpu=True);ctx=io.load(protocol_path,batch_id);store=ctx['store'];batch=ctx['batch']
    pointer=io.read(ctx['root']/'output_replay_pointer.json')
    complete=io.read(store.checked_ref(pointer['completion_ref']))
    c.require(complete['status']=='PASS_COMPLETE_BATCH_OUTPUT_REPLAY_NOT_QUALITY' and complete['batch_id']==batch_id and
        complete['batch_sha256']==io.sha(ctx['batch_path']) and complete['global_graph_sha256']==ctx['protocol']['full_plan_ref']['sha256'] and
        [row['consumer'] for row in complete['proofs']]==batch['request_ids'],'Complete fixed batch first independent replay required before closure')
    leases={key:row for key,row in ctx['plan']['RGB_groups'].items() if row['source_id'] in batch['source_ids']}
    c.require(set(consumer for row in leases.values() for consumer in row['consumers'])==set(batch['request_ids']) and
        all(set(row['consumers'])<=set(batch['request_ids']) for row in leases.values()),
        'A source RGB lease was split across batches; no release')
    base='permanent/proofs/runtime_v2/'+batch_id+'/closure'
    c.require(not store.path(base+'/launch.json','permanent').exists(),'Closure already attempted; preserve partial acceptance/release receipts')
    store.write_metadata(base+'/launch.json',dict(batch_id=batch_id,output_replay_completion_ref=pointer['completion_ref'],
        request_ids=batch['request_ids'],lease_ids=list(leases),new_model_calls=0,canonical_retention='PERMANENT_LOSSLESS_EXACT_INPUT'))
    accepted=[];released=[]
    try:
        for row in complete['proofs']:
            # The critic library independently enforces complete proof/real natural ledger/retained raw and exact canonical input.
            store.accept_consumer(row['consumer'],row['proof_ref'],complete['resource_ref'],complete['ledger_ref'])
            accepted.append(row['consumer'])
        for lease_id in leases:
            receipt=store.release_rgb(lease_id)
            c.require(receipt['RGB_present'] is False and receipt['canonical_files_retained'] is True and receipt['old_success_files_deleted']==0,
                'New-staging release did not preserve permanent/old artifacts')
            released.append(receipt)
        ref=store.write_metadata(base+'/completion.json',dict(status='PASS_BATCH_CONSUMER_CLOSURE_NEW_RGB_RELEASE_NOT_QUALITY',
            batch_id=batch_id,accepted_consumers=accepted,new_RGB_release_receipts=released,
            output_replay_completion_ref=pointer['completion_ref'],resource_ref=complete['resource_ref'],ledger_ref=complete['ledger_ref'],
            global_graph_sha256=ctx['protocol']['full_plan_ref']['sha256'],batch_sha256=io.sha(ctx['batch_path']),
            permanent_exact_inputs_and_raw_retained=True,old_success_files_deleted=0,new_model_calls=0,new_processor_encodes=0,new_media_decodes=0))
        io.save(ctx['root']/'closure_pointer.json',dict(completion_ref=ref))
    except BaseException as error:
        store.write_metadata(base+'/failure.json',dict(status='FAILED_CLOSURE_RETAIN_CANONICAL_AND_UNRELEASED_RGB',batch_id=batch_id,
            accepted_consumers=accepted,completed_new_RGB_releases=released,error=repr(error),automatic_retry=False,
            new_model_calls=0,old_success_files_deleted=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--protocol',required=True,type=Path);parser.add_argument('--batch-id',required=True)
    args=parser.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';close(args.protocol,args.batch_id)
