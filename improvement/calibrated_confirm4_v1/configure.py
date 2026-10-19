"""Freeze a human-reviewed draft and existing file bindings; no media/model work."""
import argparse
from pathlib import Path
from confirm_common import MODEL_PARAMETERS, SCHEMA, ref, read, require, save

W = Path('/home/inspur/aic_video_work')
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def default_paths():
    package = RUN/'b_score_aligned_package_v4'
    source = W/'source_clear_residual_20261018_v1/code'
    cv = W/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'
    paths = {name: package/(name+'.py') for name in ('common', 'engine', 'contracts', 'constrained_json', 'source_color')}
    paths.update({name: source/(name+'.py') for name in ('sr_common', 'prepare_v3', 'prepare_v5')})
    paths.update({name: cv/(name+'.py') for name in ('cv_contract', 'cv_tokens', 'cv_grammar')})
    paths.update({name: W/'videoxum_reference_iteration_20261013_v1/code'/(name+'.py')
                  for name in ('native_profile_01', 'native_profile_04')})
    paths.update(runtime=W/'temporal_refinement_pilot_20261011/dev_01/runtime.py',
        bw_video=RUN/'balanced_two_window_risk_v3/bw_video.py', exact_pts=RUN/'baseline_a_pts_v1/exact_pts.py',
        native_frames=RUN/'baseline_a_pts_v1/native_frames.py', sft_contract=RUN/'temporal_sft8b_v1/sft_contract.py',
        semantic_head=W/'semantic_context_production_20261016_v1/selected_head.pt', model_config=package/'config.json',
        gpu_runner=RUN/'resource_unlimited_v1_20261007/gpu_run.py')
    return paths


def freeze(draft_path, output):
    draft = read(draft_path)
    for key in ('root', 'ram_root', 'sources', 'deadline_utc', 'gpu_stages', 'cpu_threads', 'gpu_cpu_threads', 'cuda_visible_devices', 'maximum_source_seconds', 'native_admission_path'):
        require(key in draft, 'Draft requires explicit '+key)
    sources = draft['sources']; ids = [source['sid'] for source in sources]
    require(0 < len(ids) <= 4 and len(set(ids)) == len(ids), 'Fixed at most4 source IDs')
    for family in ('b0', 'verify', 'context'):
        spec = draft['gpu_stages'][family]
        require(all(key in spec for key in ('name', 'max_seconds', 'planned_output_bytes', 'capacity_reason', 'queue_seconds')),
                'Explicit GPU workload/resource registration for '+family)
    paths = default_paths(); paths.update({key: Path(value) for key, value in draft.pop('dependency_paths', {}).items()})
    refs = {key: ref(path) for key, path in paths.items()}
    model = read(paths['model_config']); model_dir = Path(model['model_dir'])
    assets = {path.name: ref(path) for path in sorted(model_dir.iterdir())
              if path.is_file() and path.suffix in ('.json', '.txt', '.jinja')}
    require(assets, 'Existing frozen processor/tokenizer assets')
    config = dict(draft, schema=SCHEMA, source_ids=ids, source_count=len(ids), dependency_refs=refs,
        processor_asset_refs=assets, implementation_refs={path.name: ref(path) for path in sorted(Path(__file__).parent.glob('*.py'))},
        model_parameters=MODEL_PARAMETERS, labels_available_to_pipeline=False,
        hostname='inspur-NP5570M5',
        python=str(W/'env/qwen3vl_isolated_20260910/bin/python'), resource_directory=str(RUN/'controller'),
        gpu_ledger=str(W/'improvement_round1/gpu_ledger.jsonl'),
        ram_cache_lifecycle='Task-owned tmpfs, retain all successful caches; no implicit cleanup, reconstruction or resume')
    save(output, config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('draft'); parser.add_argument('output')
    args = parser.parse_args(); freeze(args.draft, args.output)
