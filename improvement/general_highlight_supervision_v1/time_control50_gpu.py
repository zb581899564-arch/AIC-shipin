"""First original trained-B answer per accepted diving window; no processor rerun."""
from fractions import Fraction
import json
import math
import time
import sys
import numpy as np
import torch

from time_control50_common import ROOT,RUN,read,ref,save,checked,runtime


def main():
    rt=runtime()
    from sft_contract import verify_live_gpu_reservation
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    verify_live_gpu_reservation();torch.set_num_threads(2)
    for identity in read(ROOT/'source_input_lock.json')['code'].values():checked(identity)
    accepted=read(ROOT/'CPU_completion.json');(ROOT/'outputs').mkdir()
    model,processor,identity=rt.b_engine.load_model(read(RUN/'b_score_aligned_package_v4/config.json'))
    if (identity['logical_parameters']!=8782459120 or
        identity['base']['sha256']!='74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' or
        identity['adapter']['sha256']!='8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'):
        raise ValueError('Original actual B/TIME identity differs')
    save(ROOT/'model_identity.json',identity)
    candidates=ascii_token_candidates(processor.tokenizer);eos=model.generation_config.eos_token_id
    eos=[eos] if isinstance(eos,int) else list(eos)
    accepted_outputs=[]
    with (ROOT/'attempts.jsonl').open('x') as journal:
        for record in accepted['accepted']:
            case=read(checked(record));meta=read(checked(case['input']));name=meta['case_id']
            with np.load(checked(case['encoded']),allow_pickle=False) as data:
                encoded={key:torch.from_numpy(data[key].copy()) for key in data.files}
            encoded.update(case['non_tensor_inputs'])
            if rt.tensor_signature(encoded)!=case['detail']['tensor_signature']:
                raise ValueError('Real model input differs from accepted actual CPU tensors')
            prefix=int(encoded['input_ids'].shape[1]);lo=Fraction(meta['window_start']);hi=Fraction(meta['window_end'])
            grammar=make_prefix_constraint(processor.tokenizer,prefix,hi-lo,candidate_token_ids=candidates,eos_token_ids=eos,allow_empty=True)
            folder=ROOT/'outputs'/name;folder.mkdir()
            save(folder/'request.json',dict(CPU_acceptance=record,CPU_input=case['encoded'],
                token_prefix=prefix,source_start=str(lo),source_end=str(hi),no_labels=True))
            journal.write(json.dumps(dict(event='BEGIN',case=name))+'\n');journal.flush();start=time.monotonic()
            with torch.inference_mode():
                result=model.generate(**{k:v.cuda() if torch.is_tensor(v) else v for k,v in encoded.items()},do_sample=False,max_new_tokens=256,
                    prefix_allowed_tokens_fn=grammar,return_dict_in_generate=True,output_scores=True)
            torch.cuda.synchronize();ids=result.sequences[0,prefix:]
            raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            scores=[float(s[0,int(token)]) for s,token in zip(result.scores,ids)]
            save(folder/'raw.json',dict(raw=raw,token_ids=ids.tolist(),token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                generation_seconds=time.monotonic()-start,prefix=prefix,eos=eos))
            if len(scores)!=len(ids) or not all(math.isfinite(s) for s in scores):raise ValueError('Actual token-score denominator invalid')
            grammar.assert_complete(ids);segments,errors,warnings=rt.parse_segments(raw,hi-lo,allow_empty=True)
            if segments is None or errors:raise ValueError('Actual original parser failed; not converted to empty')
            save(folder/'acceptance.json',dict(case=name,segments=segments,warnings=warnings,
                status='LEGAL_EMPTY' if not segments else 'MODEL_OK',raw=ref(folder/'raw.json'),
                source_start=str(lo),source_end=str(hi)))
            accepted_outputs.append(ref(folder/'acceptance.json'));journal.write(json.dumps(dict(event='ACCEPTED',case=name))+'\n');journal.flush()
            print('ORIGINAL_TIME_ACCEPTED',len(accepted_outputs),accepted['windows'],flush=True)
            del result,ids,encoded
    save(ROOT/'gpu_completion.json',dict(state='ORIGINAL_TIME_FIRST_CONTROL_COMPLETE',outputs=accepted_outputs,
        actual_calls=len(accepted_outputs),new_training=0,logical_parameters=8782459120))


if __name__=='__main__':main()
