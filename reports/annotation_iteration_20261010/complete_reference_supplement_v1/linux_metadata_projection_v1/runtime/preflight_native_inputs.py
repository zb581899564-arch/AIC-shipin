"""Actual CPU native/processor parity before GPU training; no model is loaded."""
import argparse,sys,traceback
from pathlib import Path
from common import admit,helpers,require,save,sha,verify_lock
from native_runtime import encode

def execute(contract,output):
    out=Path(output);require(not out.exists(),'fresh preflight output required')
    require(out.parent.resolve()==Path(contract['config']['train_output_dir']).parent.resolve(),'preflight must stay in current experiment')
    out.mkdir(parents=True,exist_ok=False)
    report=dict(status='RUNNING_ACTUAL_CPU_NATIVE_PROCESSOR_PARITY',rows=[],model_loaded=False,new_model_calls=0,new_optimizer_updates=0,lock_sha256=contract['lock_sha'],config_sha256=contract['config_sha'])
    try:
        import torch,transformers,av
        from transformers import AutoProcessor
        require(not torch.cuda.is_initialized(),'CPU preflight unexpectedly initialized CUDA')
        unused,video,unused2,unused3=helpers(contract['config'])
        processor=AutoProcessor.from_pretrained(contract['config']['processor_dir'],local_files_only=True)
        processor.video_processor.do_sample_frames=False
        training=set(contract['schedule']['window_ids'])
        keys=sorted(set(training)|set(contract['config']['final_only_evaluation_window_ids']))
        for ix,key in enumerate(keys):
            encoded,evidence=encode(contract,key,processor,video,training=key in training)
            require(all(v.device.type=='cpu' for v in encoded.values() if hasattr(v,'device')),'non-CPU preflight tensor')
            row=dict(window_id=key,training_target_present=key in training,actual_native_and_reviewed_processor_equal=True,evidence=evidence)
            rowpath=out/('%02d.input.json'%ix);save(rowpath,row)
            report['rows'].append(dict(window_id=key,training_target_present=key in training,input_tokens=evidence['processor_identity'].get('input_tokens'),normalized_tensor_sha256=evidence['normalized_tensor_sha256'],input_receipt=dict(path=str(rowpath),sha256=sha(rowpath))))
            del encoded
            print(__import__('json').dumps(dict(window_id=key,status='PASS_ACTUAL_CPU_INPUT_PARITY',training_target_present=key in training)),flush=True)
        require(not torch.cuda.is_initialized(),'CPU preflight initialized CUDA')
        verify_lock(contract['lock_path'],contract['lock_sha'])
        report.update(status='PASS_ACTUAL_CPU_NATIVE_PROCESSOR_AND_ASSISTANT_TARGET_PARITY_NOT_TRAINING',windows=len(keys),training_windows=len(training),evaluation_windows=12,torch_version=torch.__version__,transformers_version=transformers.__version__,pyav_version=av.__version__,cuda_initialized=False)
    except BaseException as error:
        report.update(status='STOP_ACTUAL_CPU_INPUT_PARITY',failure_type=type(error).__name__,failure=str(error),traceback=traceback.format_exc(),failure_converted_to_empty=False)
        save(out/'receipt.json',report);raise
    save(out/'receipt.json',report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--lock',required=True);p.add_argument('--expected-lock',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args()
    contract=admit(a.config,a.lock,a.expected_lock,'train');execute(contract,a.output_dir)
if __name__=='__main__':main()
