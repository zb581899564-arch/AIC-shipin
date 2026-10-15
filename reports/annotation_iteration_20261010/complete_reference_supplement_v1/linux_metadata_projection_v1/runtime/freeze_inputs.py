"""Create a new Linux byte lock from admitted projected inputs; never load a model."""
import argparse
import ast
from datetime import datetime, timezone
from pathlib import Path
from common import HERE, bound, read, require, save, sha


def freeze(config_path, output):
    config_path = Path(config_path).resolve(strict=True)
    c = read(config_path)
    root = Path(c['train_output_dir']).parent.resolve()
    output = Path(output).resolve()
    require(output.parent == root and not output.exists(), 'fresh experiment-root lock required')
    require(config_path.is_relative_to(root), 'projected config must belong to experiment')
    require(c['schema'] == 'COMPLETE_SILVER_NATIVE_RUNTIME_V1', 'unsupported config')
    files = {}
    def add(path, digest=None):
        p = Path(path).resolve(strict=True)
        require(p.is_file(), 'lock member must be a file')
        actual = sha(p)
        require(digest is None or actual == digest, 'input binding differs: '+str(p))
        require(str(p) not in files or files[str(p)] == actual, 'conflicting lock member')
        files[str(p)] = actual
    def add_bound(binding):
        p = bound(binding)
        add(p, binding['sha256'])
        return p
    add(config_path)
    for p in sorted(HERE.glob('*.py')):
        add(p)
    for key in ('protocol', 'plan', 'processor_binding', 'quality_contract',
                'silver_contract', 'event_metrics', 'reference_registry', 'resource_policy'):
        add_bound(c[key])
    registry = read(bound(c['reference_registry']))
    for row in registry.get('records', registry).values():
        if row.get('reference'):
            reference = read(add_bound(row['reference']))
            for binding in reference['evidence'].values():
                add_bound(binding)
    for binding in c['target_sidecars'].values():
        add_bound(binding)
    for binding in c['source_files'].values():
        add_bound(binding)
    # Read the same literal dependency tuple used by admission. No launcher is imported.
    tree = ast.parse((HERE/'common.py').read_text(encoding='utf-8'))
    names = [ast.literal_eval(node.value) for node in ast.walk(tree)
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
             t.id == 'dependency_names' for t in node.targets)]
    require(len(names) == 1, 'unique admission dependency inventory required')
    historical = Path(c['historical_run_root']).resolve(strict=True)
    for name in names[0]:
        add(historical/name)
    # The conditional 426 stage is part of this frozen single execution.
    # Bind its inputs before training, without importing a historical launcher.
    spec = read(add_bound(c['candidate_contract']))
    require(spec['schema'] == 'FIXED_SILVER_426_FRESH_TEMPORAL_CANDIDATE_V1',
            'candidate contract schema differs')
    for key in ('plan', 'manifest', 'clock_registry', 'changed_cpu_acceptance'):
        add_bound(spec[key])
    for binding in spec['space'].values():
        add_bound(binding)
    for row in read(bound(spec['manifest']))['records']:
        add(row['source_path'], row['source_sha256'])
    for row in read(bound(spec['clock_registry']))['records']:
        add_bound(row['clock_arrays'])
    candidate_tree = ast.parse((HERE/'candidate_support.py').read_text(encoding='utf-8'))
    candidate_names = [ast.literal_eval(node.value) for node in ast.walk(candidate_tree)
                       if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
                       t.id == 'DEPENDENCIES' for t in node.targets)]
    require(len(candidate_names) == 1, 'unique candidate dependency inventory required')
    for name in candidate_names[0]:
        add(historical/name)
    strict_root = Path(spec['strict_loader_root']).resolve(strict=True)
    require(strict_root == (historical/'baseline_a_pts_v1/vendor/frozen_strict_loader').resolve(strict=True),
            'foreign strict loader root')
    for member in sorted(strict_root.rglob('*')):
        if member.is_file():
            add(member)
    model = Path(c['model_dir']).resolve(strict=True)
    index = read(model/'model.safetensors.index.json')
    for name in sorted({'config.json', 'generation_config.json', 'model.safetensors.index.json'} |
                       set(index['weight_map'].values())):
        p = (model/name).resolve(strict=True)
        require(p.parent == model, 'model member escaped model root')
        add(p)
    for row in read(bound(c['processor_binding']))['rows']:
        p = (Path(c['processor_dir'])/row['file']).resolve(strict=True)
        require(p.parent == Path(c['processor_dir']).resolve(), 'processor member escaped root')
        add(p, row['sha256'])
    for name in ('adapter_model.safetensors', 'adapter_config.json'):
        add(Path(c['initial_adapter_dir'])/name,
            c['initial_adapter_sha256'] if name == 'adapter_model.safetensors' else None)
    save(output, dict(schema='COMPLETE_SILVER_NATIVE_BYTE_LOCK_V1',
                     utc=datetime.now(timezone.utc).isoformat(), files=files))
    result = dict(status='PASS_NEW_BYTE_LOCK_CREATED_STATIC_ADMISSION_STILL_REQUIRED',
                  path=str(output), sha256=sha(output), files=len(files),
                  new_model_calls=0, new_optimizer_updates=0)
    save(output.with_name(output.stem+'.creation_receipt.json'), result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True); p.add_argument('--output', required=True)
    a = p.parse_args()
    print(__import__('json').dumps(freeze(a.config, a.output)))


if __name__ == '__main__':
    main()
