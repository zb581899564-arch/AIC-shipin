"""Metadata/cache-SHA admission, never GPU permission or model execution."""
import argparse
import os
from pathlib import Path

import pr_contract as c
import pr_io as io


def admit(protocol_path,batch_id):
    io.host(cpu=True);ctx=io.load(protocol_path,batch_id,require_admission=False)
    accepted,CPU_ref=io.CPU_acceptance(ctx);store=ctx['store'];batch=ctx['batch']
    rows=[]
    for rid,value in accepted.items():
        for ref in (value['manifest']['private_ref'],value['manifest']['visual_ref']):
            if ref:store.checked_ref(ref)
        store.checked_ref(value['proof']['original_RGB_ref'],'staging')
        rows.append(dict(consumer=rid,input_manifest_ref=value['entry']['input_manifest_ref'],
            CPU_input_proof_ref=value['entry']['CPU_input_proof_ref'],full_input_signature=value['manifest']['full_signature']))
    io.save(ctx['root']/'input_admission.json',dict(status='PASS_COMPLETE_FIXED_BATCH_INPUTS_NOT_GPU_PERMISSION',
        protocol_sha256=io.sha(ctx['protocol_path']),batch_sha256=io.sha(ctx['batch_path']),batch_CPU_admission_ref=CPU_ref,
        global_graph_sha256=ctx['protocol']['full_plan_ref']['sha256'],global_source_request_lock_ref=ctx['graph_ref'],
        consumers=rows,request_ids=batch['request_ids'],actual_model_call_budget=len(rows),
        source_id_to_original_video_id=ctx['source_video_projection'],endpoint_ids_recomputed=False,
        actual_physical_parameters=c.PARAMETERS,endpoint_model_role=ctx['protocol']['endpoint_model_role'],verify_model_role='TIME_ENABLED',
        first_RGB_input_replay_still_required=True,actual_new_model_calls=0,new_processor_encodes=0,new_media_decodes=0,optimizer_updates=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--protocol',required=True,type=Path);parser.add_argument('--batch-id',required=True)
    args=parser.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';admit(args.protocol,args.batch_id)
