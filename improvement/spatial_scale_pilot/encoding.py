"""Image-only processor path shared by the CPU equality gate and actual inference."""


def encode(processor, messages):
    from qwen_vl_utils import process_vision_info
    text = processor.apply_chat_template(messages, tokenize=False,
        add_generation_prompt=True, enable_thinking=False)
    images, videos = process_vision_info(messages, image_patch_size=16)
    if videos:
        raise ValueError('static pilot cannot silently change to video input')
    encoded = processor(text=[text], images=images, padding=True,
        truncation=False, return_tensors='pt')
    return encoded, text, len(images)
