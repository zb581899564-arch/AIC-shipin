"""Role-name independent fingerprint of the actual effective adapter bytes."""
import hashlib
import json

import torch
from peft import get_peft_model_state_dict


def fingerprint(model, role, frozen_base):
    digest = hashlib.sha256(json.dumps(frozen_base, sort_keys=True).encode())
    for name, value in sorted(get_peft_model_state_dict(model, adapter_name=role).items()):
        value = value.detach().contiguous().cpu()
        digest.update(name.encode()); digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()
