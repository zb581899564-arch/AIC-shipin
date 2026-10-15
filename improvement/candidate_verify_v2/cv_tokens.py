"""Prompt-only retargeting of accepted B0 token/vision caches; no video encode."""
import hashlib

from cv_contract import MAX_INPUT_TOKENS

VISION_KEYS = ('pixel_values_videos', 'video_grid_thw')
TOKEN_KEYS = ('input_ids', 'attention_mask')


def vision_prefix(input_ids, tokenizer):
    import torch
    if input_ids.ndim != 2 or input_ids.shape[0] != 1:
        raise ValueError('One original unpadded B0 token sequence required')
    end_id = tokenizer.convert_tokens_to_ids('<|vision_end|>')
    pad_id = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    values = input_ids[0].tolist()
    endings = [i for i, value in enumerate(values) if value == end_id]
    if not endings or pad_id not in values:
        raise ValueError('Original expanded native video token block is missing')
    prefix = input_ids[:, :endings[-1]+1]
    digest = hashlib.sha256(prefix.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
    return prefix, dict(tokens=int(prefix.shape[1]), sha256=digest,
                        vision_end_count=len(endings), video_pad_count=values.count(pad_id))


def retarget(original, tokenizer, original_prompt, new_prompt, tensor_signature):
    """Create only new text tokens; retain exact old visual tensors/timestamps."""
    import torch
    if set(original) != set(VISION_KEYS+TOKEN_KEYS):
        raise ValueError('Unexpected original model-input keys; no guessed retarget adapter')
    if (any(not isinstance(t, torch.Tensor) or t.device.type != 'cpu' for t in original.values()) or
            not torch.all(original['attention_mask'] == 1)):
        raise ValueError('Original accepted one-window CPU cache is not unpadded')
    ids = original['input_ids'][0].tolist()
    old_text = tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if old_text.count(original_prompt) != 1:
        raise ValueError('Original EMPTY_PROMPT is not unique in expanded accepted token input')
    # Token-only roundtrip checks the original expanded native timestamp text.
    # It does not call the vision processor or re-normalize any pixel.
    roundtrip = tokenizer([old_text], return_tensors='pt', padding=False, truncation=False,
                          add_special_tokens=False)
    if set(roundtrip) != set(TOKEN_KEYS) or not torch.equal(roundtrip['input_ids'], original['input_ids']):
        raise ValueError('Original expanded tokenizer roundtrip differs; stop without repair')
    new_text = old_text.replace(original_prompt, new_prompt, 1)
    tokens = tokenizer([new_text], return_tensors='pt', padding=False, truncation=False,
                       add_special_tokens=False)
    if (set(tokens) != set(TOKEN_KEYS) or tokens['input_ids'].shape[0] != 1 or
            int(tokens['input_ids'].shape[1]) > MAX_INPUT_TOKENS or
            not torch.all(tokens['attention_mask'] == 1)):
        raise ValueError('Actual new token budget/keys/padding changed; no truncation fallback')
    old_prefix, old_prefix_evidence = vision_prefix(original['input_ids'], tokenizer)
    new_prefix, new_prefix_evidence = vision_prefix(tokens['input_ids'], tokenizer)
    if not torch.equal(old_prefix, new_prefix) or old_prefix_evidence != new_prefix_evidence:
        raise ValueError('Native timestamps/expanded vision token prefix changed with new text')
    combined = {**dict(tokens), **{key: original[key] for key in VISION_KEYS}}
    old_vision = tensor_signature({key: original[key] for key in VISION_KEYS})
    if tensor_signature({key: combined[key] for key in VISION_KEYS}) != old_vision:
        raise ValueError('Original pixel/video-grid tensor signature changed')
    return dict(tokens), combined, dict(
        original_expanded_text_sha256=hashlib.sha256(old_text.encode()).hexdigest(),
        new_expanded_text_sha256=hashlib.sha256(new_text.encode()).hexdigest(),
        vision_prefix=old_prefix_evidence, unchanged_vision_tensor_signature=old_vision,
        full_tensor_signature=tensor_signature(combined),
        input_tokens=int(tokens['input_ids'].shape[1]),
        original_text_roundtrip_tokenizer_calls=1, new_prompt_tokenizer_calls=1,
        vision_processor_calls=0, media_decodes=0, original_vision_tensors_reused=True)
