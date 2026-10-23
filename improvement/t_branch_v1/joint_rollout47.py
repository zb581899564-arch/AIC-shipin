"""Explicit remaining recovery for first-rollout input-gradient hook lifecycle."""
from actor_roles33 import activate_actor, adapter_equal
from joint_rollout44 import original_greedy, run_case


def evaluation_mode(model):
    model.gradient_checkpointing_disable()
    native = model.get_base_model() if hasattr(model, 'get_base_model') else model
    # Transformers disable_input_require_grads is not idempotent before the
    # first enable call. A fresh inference model legitimately has no hook.
    if hasattr(native, '_require_grads_hook'):
        model.disable_input_require_grads()


def rollout(model, processor, rt, source, folder, sampling):
    folder.mkdir()
    greedy, sampled, receipts = {}, {}, {}
    evaluation_mode(model)
    activate_actor(model, 'actor')
    unchanged = adapter_equal(model)
    for case in source.cases:
        gdir = folder / (case.name + '_greedy')
        if unchanged:
            g, gr = original_greedy(case, gdir)
        else:
            g, gr = run_case(model, processor, rt, case, gdir, None)
        s, sr = run_case(model, processor, rt, case, folder / (case.name + '_sample'), sampling)
        greedy[case.name], sampled[case.name] = source.selection(case, g), source.selection(case, s)
        receipts[case.name] = dict(greedy=gr, sampled=sr)
        print('JOINT47_TRAJECTORY', source.sid, case.name, s['status'], flush=True)
    return greedy, sampled, receipts
