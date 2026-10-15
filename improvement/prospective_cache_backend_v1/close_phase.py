"""Remaining-only close callback; original PR5 output QA and graph stay frozen."""
import argparse
import importlib.util
import os
from pathlib import Path
import sys

from backend import checked_external, open_store, read, require, sha


def close(protocol_path, batch_id, phase_admission_path):
    admission_path = Path(phase_admission_path).absolute(); admission = read(admission_path)
    require(admission['schema'] == 'TEMPORAL_PRODUCTION_CLOSE_PHASE_V1' and
            admission['status'] == 'MAIN_APPROVED_REMAINING_SOURCE_AND_CLOSE_PHASES' and
            batch_id in admission['remaining_close_batch_ids'], 'This future close callback is not admitted')
    own = Path(__file__).resolve()
    require(checked_external(admission['close_driver_ref']).resolve() == own,
            'Actual new close driver must be byte-bound')
    checked_external(admission['backend_code_ref'])
    checked_external(admission['quiescent_handoff_ref'])
    controller_path=checked_external(admission['controller_registration_ref']); controller=read(controller_path)
    require(controller['prospective_close_phase_code_ref']==admission['close_driver_ref'] and
            controller['prospective_backend_code_ref']==admission['backend_code_ref'] and
            Path(controller['prospective_close_phase_admission_path']).absolute()==admission_path and
            Path(controller['prospective_backend_admission_path']).absolute()==Path(admission['backend_admission_ref']['path']).absolute(),
            'Actual new close/backend callbacks must be declared by this exact controller')
    original_io = checked_external(admission['original_runtime_io_ref'])
    sys.path.insert(0, str(original_io.parent))
    spec = importlib.util.spec_from_file_location('pr_io', original_io)
    if 'pr_io' in sys.modules:
        require(Path(sys.modules['pr_io'].__file__).resolve() == original_io.resolve(), 'Runtime namespace shadowed')
        io = sys.modules['pr_io']
    else:
        io = importlib.util.module_from_spec(spec); sys.modules['pr_io'] = io; spec.loader.exec_module(io)
    io.host(cpu=True)
    require(checked_external(admission['runtime_protocol_ref']).resolve() == Path(protocol_path).resolve(),
            'Original runtime protocol changed')
    ctx = io.load(protocol_path, batch_id); old_store = ctx['store']; batch = ctx['batch']
    require(ctx['protocol']['full_plan_ref']['sha256'] == admission['global_graph_sha256'], 'Original graph changed')
    extension_path = checked_external(admission['backend_admission_ref'])
    store = open_store(type(old_store), old_store.base, extension_path)
    pointer = io.read(ctx['root']/'output_replay_pointer.json')
    complete = read(store.checked_ref(pointer['completion_ref']))
    require(complete['status'] == 'PASS_COMPLETE_BATCH_OUTPUT_REPLAY_NOT_QUALITY' and complete['batch_id'] == batch_id and
            complete['batch_sha256'] == io.sha(ctx['batch_path']) and
            complete['global_graph_sha256'] == admission['global_graph_sha256'] and
            [row['consumer'] for row in complete['proofs']] == batch['request_ids'], 'Complete original output QA required')
    leases = {key: row for key, row in ctx['plan']['RGB_groups'].items() if row['source_id'] in batch['source_ids']}
    require(set(item for row in leases.values() for item in row['consumers']) == set(batch['request_ids']) and
            all(set(row['consumers']) <= set(batch['request_ids']) for row in leases.values()), 'Source lease cannot split batches')
    # Any begun old close must have completed naturally before handoff. A failed
    # partial old close is not automatically promoted/retried by this callback.
    old_launch = old_store.path('permanent/proofs/runtime_v5/'+batch_id+'/closure/launch.json', 'permanent')
    require(not old_launch.exists() and not (ctx['root']/'closure_pointer.json').exists(),
            'Old attempted/completed close requires explicit original success reuse; do not retry it')
    base = 'permanent/proofs/prospective_backend_v1/'+batch_id+'/closure'
    provenance = dict(prospective_phase_ref=dict(path=str(admission_path), sha256=sha(admission_path)),
        prospective_backend_ref=store._extension_ref, actual_close_driver_ref=admission['close_driver_ref'],
        original_runtime_protocol_ref=admission['runtime_protocol_ref'], quiescent_handoff_ref=admission['quiescent_handoff_ref'])
    store.write_metadata(base+'/launch.json', dict(batch_id=batch_id, output_replay_completion_ref=pointer['completion_ref'],
        request_ids=batch['request_ids'], lease_ids=list(leases), new_model_calls=0, **provenance))
    accepted = []; released = []; reused_acceptance = []; reused_release = []
    try:
        rows = store._rows()
        old_accept = {row['consumer']: row for row in rows if row.get('event') == 'CONSUMER_ACCEPTED'}
        require(len(old_accept) == len([row for row in rows if row.get('event') == 'CONSUMER_ACCEPTED']), 'Duplicate acceptance')
        for row in complete['proofs']:
            consumer = row['consumer']
            if consumer in old_accept:
                previous = old_accept[consumer]
                require(previous['proof_ref'] == row['proof_ref'] and previous['resource_ref'] == complete['resource_ref'] and
                        previous['ledger_ref'] == complete['ledger_ref'], 'Existing acceptance belongs to another proof')
                manifest, manifest_ref = store.canonical_byte_binding(consumer)
                require(manifest_ref == previous['input_manifest_ref'], 'Existing successful canonical input changed')
                for key in ('proof_ref', 'resource_ref', 'ledger_ref'): store.checked_ref(previous[key])
                for ref in previous['retained_evidence_refs'].values(): store.checked_ref(ref)
                reused_acceptance.append(previous)
            else:
                store.accept_consumer(consumer, row['proof_ref'], complete['resource_ref'], complete['ledger_ref'])
            accepted.append(consumer)
        for lease_id in leases:
            state = store.staging_state(lease_id)
            if state['state'] == 'RELEASED':
                receipt = state['release_receipt']; reused_release.append(receipt)
            else:
                require(state['state'] == 'LIVE_STAGING', 'Partial release attempt cannot be retried')
                receipt = store.release_rgb(lease_id)
            require(receipt['RGB_present'] is False and receipt['canonical_files_retained'] is True and
                    receipt['old_success_files_deleted'] == 0 and receipt['consumers'] == leases[lease_id]['consumers'],
                    'Release changed frozen dependencies or permanent retention')
            released.append(receipt)
        result = dict(status='PASS_BATCH_CONSUMER_CLOSURE_NEW_RGB_RELEASE_NOT_QUALITY', batch_id=batch_id,
            accepted_consumers=accepted, new_RGB_release_receipts=released,
            reused_original_acceptance_rows=reused_acceptance, reused_original_release_rows=reused_release,
            actual_new_acceptance_count=len(accepted)-len(reused_acceptance),
            actual_new_RGB_release_count=len(released)-len(reused_release),
            output_replay_completion_ref=pointer['completion_ref'], resource_ref=complete['resource_ref'], ledger_ref=complete['ledger_ref'],
            global_graph_sha256=admission['global_graph_sha256'], batch_sha256=io.sha(ctx['batch_path']),
            permanent_exact_inputs_and_raw_retained=True, old_success_files_deleted=0,
            new_model_calls=0, new_processor_encodes=0, new_media_decodes=0, **provenance)
        ref = store.write_metadata(base+'/completion.json', result)
        io.save(ctx['root']/'closure_pointer.json', dict(completion_ref=ref))
        return ref
    except BaseException as error:
        store.write_metadata(base+'/failure.json', dict(status='FAILED_PROSPECTIVE_CLOSE_RETAIN_ALL', batch_id=batch_id,
            accepted_consumers=accepted, completed_new_RGB_releases=released, error=repr(error), automatic_retry=False, **provenance))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--batch-id', required=True); parser.add_argument('--phase-admission', required=True, type=Path)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    close(args.protocol, args.batch_id, args.phase_admission)
