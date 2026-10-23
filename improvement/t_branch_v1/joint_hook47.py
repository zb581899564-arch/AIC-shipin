"""Targeted real Transformers lifecycle regression, no actual8B or optimizer."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch
from transformers import PreTrainedModel, PretrainedConfig

from joint_rollout47 import evaluation_mode
from t_io import ROOT, save


class Toy(PreTrainedModel):
    def __init__(self):
        super().__init__(PretrainedConfig())
        self.embedding = torch.nn.Embedding(3, 2)

    def get_input_embeddings(self):
        return self.embedding

    def gradient_checkpointing_disable(self):
        pass


def main():
    out = ROOT / 'joint_hook47'; out.mkdir()
    model = Toy()
    evaluation_mode(model)
    if hasattr(model, '_require_grads_hook'):
        raise ValueError('Fresh inference role unexpectedly created an input hook')
    model.enable_input_require_grads()
    evaluation_mode(model)
    evaluation_mode(model)
    save(out / 'completion.json', dict(state='PASS_REAL_TRANSFORMERS_INITIAL_AND_REPEATED_HOOK_LIFECYCLE',
        actual8B_calls=0, updates=0, scientific_recipe_changed=False))


if __name__ == '__main__':
    main()
