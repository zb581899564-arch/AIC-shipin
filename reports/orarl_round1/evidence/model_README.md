---
library_name: transformers
license: apache-2.0
pipeline_tag: image-text-to-text
base_model:
  - Qwen/Qwen3.5-4B
tags:
  - transformers
  - vllm
  - video
  - multimodal
  - reinforcement-learning
  - temporal-grounding
  - object-tracking
  - video-segmentation
  - visual-question-answering
  - spatial-reasoning
  - qwen3.5
---

# Video-ORA-4B

[[🏠 Homepage](https://orarl.github.io/)] [[📖 Arxiv Paper](https://arxiv.org/abs/2608.20492)] [[🤗 Evaluation Data](https://huggingface.co/datasets/OraRL/OraRL-Data/tree/main/OraRL-eval-data)] [[💻 Code](https://github.com/HVision-NKU/OraRL)]

We release **Video-ORA-4B**, the 9B model trained with **OraRL (Annotations as
Rollouts)** for **unified video understanding**.

Starting from [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), OraRL
post-training equips one model to handle seven task families with direct,
task-native answers and no chain-of-thought decoding.

## Supported task families

- Temporal grounding
- Visual tracking
- Image and video segmentation
- Spatial grounding
- Spatial-temporal grounding
- Video question answering
- Spatial intelligence

## Model summary

| Property | Value |
| --- | --- |
| Architecture | `Qwen3_5ForConditionalGeneration` |
| Parameters | 4B |
| Weight dtype | BF16 |
| Native context length | 262,144 tokens |
| Base model | [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) |
| Post-training | OraRL annotation-augmented on-policy reinforcement learning |
| Tested serving | Transformers 5.5.4 and vLLM 0.19.1 |

## Results

### Dataset-level comparison

<a href="https://github.com/HVision-NKU/OraRL#results">
<picture>
  <source media="(prefers-color-scheme: dark)"
          srcset="https://huggingface.co/OraRL/Video-ORA-4B/resolve/main/assets/video_ora_benchmark_matrix_dark.svg">
  <source media="(prefers-color-scheme: light)"
          srcset="https://huggingface.co/OraRL/Video-ORA-4B/resolve/main/assets/video_ora_benchmark_matrix_light.svg">
  <img src="https://huggingface.co/OraRL/Video-ORA-4B/resolve/main/assets/video_ora_benchmark_matrix_light.svg"
       alt="Dataset-level benchmark matrix comparing Video-ORA with multimodal baselines"
       width="100%">
</picture>
</a>

Video-ORA-4B delivers strong compact-model results in the matched seven-family comparison without chain-of-thought
decoding. Best and second-best values are highlighted per row; `†` denotes an
original-report value whose frame, prompt, split, or decoding settings may
differ. Averages require complete family coverage.

See the [OraRL repository](https://github.com/HVision-NKU/OraRL),
[project page](https://orarl.github.io/), and
[paper](https://arxiv.org/abs/2608.20492) for complete benchmark protocols and
source attribution.

## Quick start

### vLLM serving

```bash
pip install "vllm==0.19.1" openai

vllm serve OraRL/Video-ORA-4B \
  --served-model-name Video-ORA-4B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --media-io-kwargs '{"video": {"num_frames": -1}}' \
  --limit-mm-per-prompt '{"image": 1, "video": 1}'
```

Reduce `--max-model-len` if KV-cache memory is limited. Increase
`--tensor-parallel-size` for multi-GPU serving. Model-weight loading occupies
approximately **8.6 GiB** in the tested BF16 vLLM environment; this is not a
full peak-memory measurement.

Send an OpenAI-compatible video request:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
response = client.chat.completions.create(
    model="Video-ORA-4B",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "video_url",
                    "video_url": {
                        "url": "https://orarl.github.io/assets/orarl-teaser.mp4"
                    },
                },
                {
                    "type": "text",
                    "text": "Describe the video and answer the question directly.",
                },
            ],
        }
    ],
    max_tokens=128,
    temperature=0.0,
    extra_body={
        "top_k": 20,
        "chat_template_kwargs": {"enable_thinking": False},
        "mm_processor_kwargs": {"fps": 2, "do_sample_frames": True},
    },
)
print(response.choices[0].message.content)
```

Replace the demo URL with your own accessible video URL. For local files,
launch vLLM with an appropriate `--allowed-local-media-path`.

### Transformers server

Qwen3.5 requires a recent Transformers version:

```bash
pip install "transformers[serving] @ git+https://github.com/huggingface/transformers.git@main"
pip install accelerate torchvision pillow

transformers serve \
  --force-model OraRL/Video-ORA-4B \
  --port 8000 \
  --continuous-batching
```

The checkpoint also contains the tokenizer, processor configuration, generation
configuration, and chat template required by compatible Transformers and vLLM
releases. Task-specific prompts and output schemas are documented on the
[project page](https://orarl.github.io/).

## Intended use

Video-ORA-4B is intended for research on structured image/video perception,
benchmark evaluation, and task-specific adaptation. Use direct answer prompts
with `enable_thinking=False` to match the reported evaluation protocol.

Out-of-scope uses include safety-critical decisions, identity inference,
surveillance deployment, or use that violates the licenses or consent
requirements of upstream media.

## Training data

Training uses public training splits from the task families described in the
paper. Evaluation identities, questions, and media anchors are excluded during
mixture construction. Dataset and media licenses remain governed by their
original sources; no training or benchmark media are distributed with this
checkpoint.

## Limitations

Video-ORA-4B is a research checkpoint optimized for structured video and
spatial-understanding tasks. It may produce malformed task-specific outputs,
hallucinate visual details, or inherit limitations and biases from its base
model and training data. It has not been validated for safety-critical or
high-stakes use.

## License

The checkpoint is released under the Apache License 2.0. It is derived from
[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), which is also distributed
under Apache 2.0.

## Citation

```bibtex
@article{li2026orarl,
  title   = {Annotations as Rollouts: Efficient and Scalable
             Reinforcement Learning for Video MLLMs},
  author  = {Li, Yunheng and Mu, Guohong and Li, Hao and
             Qian, Shengsheng and Zhang, Dingwen and Hou, Qibin
             and Cheng, Ming-Ming},
  journal = {arXiv preprint arXiv:2608.20492},
  year    = {2026},
  url     = {https://arxiv.org/abs/2608.20492}
}
```
