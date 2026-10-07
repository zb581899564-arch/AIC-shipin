"""Complete optional-empty assistant targets; UNKNOWN has no training target."""
from contracts import answer_string
from video_contract import encode
import json

def from_teacher_record(record):
    if record.get('status')!='PASS_WEAK_COMPLETE_WINDOW_TARGET' or record.get('sft_eligible') is not True or record.get('uncertain') is not False:
        raise ValueError('Teacher record is not eligible complete-window supervision')
    observation=record['actual_observation']
    if observation.get('all_planned_frames_delivered') is not True or record.get('parsed_answer',{}).get('observation_scope',{}).get('all_provided_frames_reviewed') is not True:
        raise ValueError('Full provided observation was not reviewed')
    segments=json.loads(record['target_json'])['segments']
    if (segments==[]) != (record.get('explicit_no_highlight') is True):
        raise ValueError('Teacher empty semantics disagree with target')
    label=dict(observation_complete=True,status='OBSERVED_EMPTY' if not segments else 'OBSERVED_POSITIVE',segments=segments)
    target_text(label,record['window']['window_duration_sec'])
    return label

def target_text(label, duration):
    if label.get('observation_complete') is not True or label.get('status') not in ('OBSERVED_POSITIVE','OBSERVED_EMPTY'):
        raise ValueError('Only complete observed supervision has an SFT target')
    segments=label.get('segments')
    if (label['status']=='OBSERVED_EMPTY') != (segments==[]):
        raise ValueError('Observed label status disagrees with segment emptiness')
    return answer_string(segments,duration,allow_empty=True)

def build_target(processor, prompt, frames, metadata, label, duration, video_size, max_input=16384, *, native_plan, source_fps):
    import torch
    answer=target_text(label,duration)
    suffix=answer+'<|im_end|>\n'
    shared=dict(videos=[frames],video_metadata=[metadata],video_size=video_size,max_input=max_input)
    from exact_pts import exact_native_pts, verify_native_encoding
    identities=[]
    def encoded_text(text):
        with exact_native_pts(processor,native_plan,source_fps) as identity:
            value=encode(processor,text=[text],**shared)
            verify_native_encoding(processor,value,identity)
        identities.append(identity)
        return value
    head=encoded_text(prompt)
    full=encoded_text(prompt+suffix)
    prefix=int(head['input_ids'].shape[1])
    if not torch.equal(full['input_ids'][0,:prefix],head['input_ids'][0]):
        raise ValueError('Assistant prefix differs from prompt input')
    for key in ('pixel_values_videos','video_grid_thw'):
        if not torch.equal(full[key],head[key]):raise ValueError('Video encoding changed between target and prompt')
    from sft_contract import assistant_labels
    mask=assistant_labels(full['input_ids'][0].tolist(),full['attention_mask'][0].tolist(),head['input_ids'][0].tolist(),head['attention_mask'][0].tolist())
    decoded=processor.tokenizer.decode(mask['assistant_token_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if decoded!=suffix:raise ValueError('Exact assistant target token boundary changed')
    full['labels']=torch.tensor([mask['tail_labels']],dtype=torch.long)
    full['logits_to_keep']=mask['logits_to_keep']
    return full,dict(answer=answer,assistant_tokens=int(full['input_ids'].shape[1])-prefix,
                     input_tokens=int(full['input_ids'].shape[1]),allow_empty=True,exact_pts_encoding=identities)
