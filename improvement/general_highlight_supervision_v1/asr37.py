"""First whole-source transcripts on new sources; frozen old tiny core, no pooling."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import hashlib
from pathlib import Path
import time
import numpy as np
import torch

from common import ROOT,read,ref,save
from pilot_common28 import checked
from source_audio36 import TARGET,OLD,old_helpers


def main():
    sources=[read(checked(r)) for r in read(TARGET/'input_acceptance.json')['accepted']]
    if len(sources)<3:raise ValueError('Fewer than three original sources aligned; no semantic claim')
    helpers,helper_ref=old_helpers()
    weights=read(OLD/'download_completion.json')['model_ref'];checked(weights)
    if weights['sha256']!='65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9':
        raise ValueError('Original authorized Whisper tiny differs')
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    module,functions,proof=helpers.original_modules(OLD/'author')
    state=torch.load(weights['path'],map_location='cpu',weights_only=True)
    model=module.Whisper(module.ModelDimensions(**state['dims']));model.load_state_dict(state['model_state_dict'],strict=True)
    model=model.float().eval().requires_grad_(False)
    count=sum(p.numel() for p in model.parameters());total=8782557449+count
    if total>9000000000 or torch.cuda.is_initialized():raise ValueError('CPU/parameter contract differs')
    vocab,special,languages,_=helpers.vocabulary(OLD/'author',model)
    save(TARGET/'ASR_registration.json',dict(sources=[ref(TARGET/s['sid']/'acceptance.json') for s in sources],
        original_model=weights,actual_ASR_parameters=count,combined_full_baseline_parameters=total,
        unchanged_tensor_helpers=helper_ref,unchanged_tensor_core_proof=proof,
        profile='Original fixedgreedy128/30sec without word timestamps; confidence/abstention thresholds unchanged',
        new_information='Whole-source ordered transcript chunks; not Whisper pooled latent or old excerpt-only fusion',
        no_new_dependencies=True,CPU_wall_budget_seconds=1200,no_training=True,
        old7_LVSum_metrics_exposed_not_reused_as_new_validation=True,
        current_sources_previously_unmodeled=True,ASR_is_not_human_ground_truth=True,
        no_automatic_Qwen_or_production=True))
    before={name:hashlib.sha256(x.detach().contiguous().numpy().tobytes()).hexdigest() for name,x in model.state_dict().items()}
    (TARGET/'asr').mkdir();started=time.monotonic();outputs=[];summary=[]
    for source in sources:
        usable=0;duration=0.;observed_duration=0.
        for chunk in source['chunks']:
            if time.monotonic()-started>1200:raise TimeoutError('Fixed whole-source CPU ASR budget elapsed; successes retained')
            with np.load(checked(chunk['wave']),allow_pickle=False) as data:wave=torch.from_numpy(data['wave'].copy())
            if chunk['observed_fraction']<.95:
                result=dict(status='VALID_ASR_ABSTAIN_INSUFFICIENT_OBSERVED_AUDIO',raw_text='',new_decoder_call=False)
            else:
                mel=functions['log_mel_spectrogram'](functions['pad_or_trim'](wave))
                if list(mel.shape)!=[80,3000] or not torch.isfinite(mel).all():raise ValueError('Original mel input differs')
                result=helpers.transcribe(model,mel,vocab,special,languages)
                result['new_decoder_call']=True
            result.update(sid=source['sid'],index=chunk['index'],start_exact=chunk['start_exact'],end_exact=chunk['end_exact'],
                waveform_acceptance=chunk,model_unchanged=True,no_human_labels_used=True,
                word_time_precision='NONE: only the exact30sec chunk interval; no invented word alignment')
            path=TARGET/'asr'/(source['sid']+f"_{chunk['index']:03d}.json");save(path,result);outputs.append(ref(path))
            length=float(__import__('fractions').Fraction(chunk['end_exact'])-__import__('fractions').Fraction(chunk['start_exact']))
            duration+=length
            if result['status']=='ASR_TRANSCRIPT_AVAILABLE_UNVERIFIED_TEXT_NOT_GROUND_TRUTH':
                usable+=1;observed_duration+=length
            print('ASR_CHUNK_ACCEPTED',source['sid'],chunk['index'],result['status'],flush=True)
        summary.append(dict(sid=source['sid'],chunks=len(source['chunks']),usable=usable,
            accepted_text_duration=observed_duration,source_duration=duration))
    after={name:hashlib.sha256(x.detach().contiguous().numpy().tobytes()).hexdigest() for name,x in model.state_dict().items()}
    if before!=after or torch.cuda.is_initialized():raise ValueError('Frozen CPU model changed')
    save(TARGET/'ASR_completion.json',dict(state='NEW_WHOLE_SOURCE_ASR_COMPLETE_NOT_HIGHLIGHT_QUALITY_PROOF',
        outputs=outputs,sources=summary,actual_ASR_parameters=count,full_parameters=total,
        CPU_seconds=time.monotonic()-started,new_GPU_calls=0,updates=0,
        no_execution_failure_to_empty=True,no_original_data_or_raw_transcripts_sent_to_closed_service=True,
        no_automatic_Qwen_or426=True))
    print('WHOLE_SOURCE_ASR_COMPLETE',summary,flush=True)


if __name__=='__main__':main()
