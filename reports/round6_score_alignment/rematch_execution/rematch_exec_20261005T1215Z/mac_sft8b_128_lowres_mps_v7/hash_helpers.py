import hashlib
from sft_contract import require

def canonical_frozen_hash(model, torch):
    parameters = {}
    seen = set()
    for name, parameter in model.named_parameters(remove_duplicate=False):
        if id(parameter) in seen or 'lora_' in name:
            continue
        seen.add(id(parameter))
        require(not parameter.requires_grad, 'base/vision became trainable during reload')
        name = name.removeprefix('base_model.model.').replace('.base_layer.', '.')
        require(name not in parameters, 'ambiguous canonical frozen parameter')
        parameters[name] = parameter
    digest = hashlib.sha256()
    count = 0
    for name, parameter in sorted(parameters.items()):
        digest.update(name.encode())
        digest.update(str(tuple(parameter.shape)).encode())
        digest.update(str(parameter.dtype).encode())
        flat = parameter.detach().reshape(-1)
        for offset in range(0, flat.numel(), 1 << 22):
            digest.update(flat[offset:offset+(1 << 22)].contiguous().view(torch.uint8).cpu().numpy().tobytes())
        count += parameter.numel()
    return {'sha256': digest.hexdigest(), 'parameters': count,
            'method': 'sorted canonical names and all unique frozen parameter bytes'}
