"""Bind declared task text to both encoder detail and actual prefix tokens."""
import hashlib


def prompt_binding(tokenizer, input_ids, detail, expected_prompt, task, forbidden_prompt=None):
    if not isinstance(expected_prompt, str) or not expected_prompt.strip():
        raise ValueError('Explicit nonempty task prompt is required')
    if task == 'VERIFY' and expected_prompt == forbidden_prompt:
        raise ValueError('VERIFY cannot use the coarse selection task prompt')
    digest = hashlib.sha256(expected_prompt.encode('utf8')).hexdigest()
    if detail.get('prompt_sha256') != digest:
        raise ValueError('Encoder task differs from the request prompt')
    values = input_ids.tolist() if hasattr(input_ids, 'tolist') else input_ids
    if len(values) != 1 or not values[0]:
        raise ValueError('A single nonempty actual prefix is required')
    decoded = tokenizer.decode(values[0], skip_special_tokens=False,
                               clean_up_tokenization_spaces=False)
    if expected_prompt not in decoded:
        raise ValueError('Actual input tokens do not contain the complete declared task')
    return dict(task=task, expected_prompt_sha256=digest,
                encoder_prompt_sha256=detail['prompt_sha256'],
                decoded_prefix_sha256=hashlib.sha256(decoded.encode('utf8')).hexdigest(),
                complete_task_in_actual_tokens=True, prefix_tokens=len(values[0]))
