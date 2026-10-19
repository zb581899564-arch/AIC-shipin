"""CONDITIONAL frozen semantic09 head application; no labels or retraining."""
import sys
from common_runtime import *
from production_semantic10 import checked_registration, checked_cpu, IDS, QUERY


def main():
    import numpy as np
    import torch
    sys.path.insert(0,str(ROOT))
    from semantic_oof09 import transform
    from monotone_head06 import ResidualHead,native_prediction
    from score_residual_head_v1.contracts import build_contract
    torch.set_num_threads(2)
    reg = checked_registration(); cpu = checked_cpu()
    feature = read(ROOT/'feature_completion.json')
    require(feature['status'] == 'PASS_ALL426_NEW_SEMANTIC_CONTEXT_FEATURES' and len(feature['sources']) == 426 and
            {s['id'] for s in feature['sources']} == IDS, 'Complete actual426 semantic generation')
    require(feature['registration_sha256'] == sha(ROOT/'production_registration.json') and
            feature['query_manifest_sha256'] == sha(QUERY/'cpu_acceptance.json') and feature['selected_view'] == reg['selected_view'], 'Frozen semantic feature/view binding')
    require(not (ROOT/'head_output_acceptance.json').exists(), 'Successful complete head stage cannot be relaunched')
    model = ResidualHead(reg['feature_dimension'],8)
    model.load_state_dict(torch.load(reg['selected_head']['path'],map_location='cpu',weights_only=True)); model.eval()
    require(8782459120+model.parameter_count == reg['actual_resident_parameters'] <= 9_000_000_000, 'Actual resident parameter budget')
    actual_cpu = {s['id']:s for s in cpu['sources']}; outputs = []
    for source in feature['sources']:
        sid = source['id']; accepted = actual_cpu[sid]
        require(source['native_sha256'] == accepted['native_sha256'] and source['clock_sha256'] == accepted['clock_sha256'], 'Semantic/native source mapping')
        language_path = ROOT/'features'/sid/'language.npy'; yesno_path = ROOT/'features'/sid/'yes_no.npy'
        require(sha(language_path) == source['language_sha256'] and sha(yesno_path) == source['yes_no_sha256'], 'Frozen actual semantic feature bytes')
        language = np.load(language_path); yesno = np.load(yesno_path); n = np.load(ROOT/'inputs'/sid/'native.npz')
        require(language.shape == (accepted['feature_cells'],4096) and yesno.shape == (accepted['feature_cells'],2) and
                np.isfinite(language).all() and np.isfinite(yesno).all(), 'Actual target-specific language/pair shapes')
        x = transform(language,yesno,n,reg['selected_view'])
        require(x.shape == (accepted['feature_cells'],reg['feature_dimension']), 'Exact external selected transform')
        contract = build_contract(n['groups'].tolist(),n['baseline'].tolist(),[None]*len(n['baseline']),len(x),read(ROOT/'inputs'/sid/'clock.json')['normalized_exact_pts'])
        directory = ROOT/'head_outputs'/sid; directory.mkdir(parents=True,exist_ok=True)
        path = directory/'output.npz'
        if path.exists():
            saved = np.load(path)
            require(str(saved['weights_sha256'].item()) == reg['selected_head']['sha256'] and
                    str(saved['language_sha256'].item()) == source['language_sha256'] and
                    str(saved['yes_no_sha256'].item()) == source['yes_no_sha256'] and
                    str(saved['selected_view'].item()) == reg['selected_view'], 'Saved successful CPU head input binding')
            residual = saved['residual']; mask = saved['selected_native']
            require(residual.shape == (len(x),) and np.isfinite(residual).all() and mask.shape == n['baseline'].shape and mask.dtype == np.bool_, 'Saved successful head output domain')
            require(tuple(mask.tolist()) == native_prediction(torch.from_numpy(residual),contract), 'Saved native expansion replay')
        else:
            require(not (directory/'acceptance.json').exists(), 'Orphan head proof blocks recomputation')
            with torch.no_grad(): residual = model(torch.from_numpy(x)).detach().numpy()
            mask = np.asarray(native_prediction(torch.from_numpy(residual),contract),dtype=np.bool_)
            with path.open('xb') as handle:
                np.savez(handle,residual=residual,selected_native=mask,weights_sha256=reg['selected_head']['sha256'],
                         language_sha256=source['language_sha256'],yes_no_sha256=source['yes_no_sha256'],selected_view=reg['selected_view'])
                handle.flush(); os.fsync(handle.fileno())
        # Independent direct predicate in actual native ordinal order, without
        # contract unit expansion. Equivalent at ties: only residual >1 adds.
        direct = n['baseline'] | (residual[n['groups']] > 1.)
        require(np.array_equal(mask,direct) and bool((mask | ~n['baseline']).all()), 'Independent native replay or protected baseline retention failed')
        rec = dict(id=sid,frames=len(mask),selected=int(mask.sum()),baseline=int(n['baseline'].sum()),
                   added=int((mask&~n['baseline']).sum()),removed=int((~mask&n['baseline']).sum()),sha256=sha(path),
                   selected_view=reg['selected_view'],weights_sha256=reg['selected_head']['sha256'],independent_direct_native_equal=True)
        proof = directory/'acceptance.json'
        if proof.exists(): require(read(proof) == rec, 'Saved head source proof changed')
        else: write(proof,rec)
        outputs.append(rec)
    require(len(outputs) == 426 and {s['id'] for s in outputs} == IDS and all(s['removed'] == 0 for s in outputs), 'Complete426 original baseline preservation')
    write(ROOT/'head_output_acceptance.json',dict(status='PASS_FROZEN_HEAD_ALL426_FIRST_NATIVE_OUTPUT_REPLAY',sources=outputs,
          actual_resident_parameters=reg['actual_resident_parameters'],selected_view=reg['selected_view'],
          selected_head_sha256=reg['selected_head']['sha256'],new_training_updates=0,new_language_generations=0,labels_read=False,
          quality_scope='Historically exposed source-isolated OOF; final25 postfit quality and official score UNKNOWN'))


if __name__ == '__main__':
    try: main()
    except BaseException as error:
        import traceback
        failure = ROOT/('semantic_apply10_failure_%s.json' % os.getpid())
        if not failure.exists(): write(failure,dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
