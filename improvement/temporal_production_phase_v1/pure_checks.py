"""Only new adapter/provenance invariants, with in-memory synthetic stores."""
import ast
from pathlib import Path
from types import ModuleType, SimpleNamespace


def run(module, source_text):
    tree = ast.parse(source_text)
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                   ((isinstance(node, ast.Import) and any(name.name.split('.')[0] in
                     {'torch', 'av', 'numpy', 'subprocess'} for name in node.names)) or
                    (isinstance(node, ast.ImportFrom) and (node.module or '').split('.')[0] in
                     {'torch', 'av', 'numpy', 'subprocess'})) for node in ast.walk(tree))
    assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign))]
    assert not any(isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and
                   target.value.id in {'original', 'original_io', 'backend'}
                   for node in assignments for target in (node.targets if isinstance(node, ast.Assign) else [node.target]))

    original = ModuleType('synthetic_original_only')
    old_io = SimpleNamespace(marker='OLD')
    original.__dict__['io'] = old_io
    exec('def helper():\n    return io.marker\ndef prepare(reg, source_id):\n    return helper(), reg, source_id\n', original.__dict__)
    adapted = module.prepare_adapter(original, SimpleNamespace(marker='NEW'))
    assert adapted({'synthetic': True}, 'S') == ('NEW', {'synthetic': True}, 'S')
    assert original.prepare({}, 'S')[0] == 'OLD' and original.io is old_io
    assert adapted.__code__ is original.prepare.__code__

    class SyntheticStore:
        def __init__(self):
            self.writes = []
            self.inputs = []

        def write_metadata(self, relative, value):
            assert relative not in [row[0] for row in self.writes]
            self.writes.append((relative, value))
            return {'relative': relative, 'synthetic_only': True}

        def save_input(self, *args):
            self.inputs.append(args)
            return {'synthetic_only': True}

    store = SyntheticStore()
    refs = {'prospective_phase_ref': {'path': 'new-source.py', 'sha256': 'a'*64},
            'prospective_backend_ref': {'path': 'admission.json', 'sha256': 'b'*64},
            'original_preparation_code_ref': {'path': 'old-prepare.py', 'sha256': 'c'*64}}
    writer = module.ProducerStore(store, refs, {'new-source.py': 'a'*64, 'backend.py': 'd'*64})
    typed = {'decision': 'UNKNOWN', 'actual_model_call': False, 'original': '1/2'}
    writer.write_metadata('permanent/proofs/R_structural_unknown.json', typed)
    assert store.writes[0][0].endswith('_producer_provenance.json')
    assert store.writes[0][1]['prospective_phase_ref'] == refs['prospective_phase_ref']
    assert store.writes[1][1] is typed and store.writes[1][1] == typed
    writer.write_metadata('permanent/proofs/source_S_completion.json', {'status': 'SYNTHETIC_NOT_PRODUCTION'})
    assert store.writes[-1][1]['structural_producer_provenance_refs']
    assert store.writes[-1][1]['original_preparation_code_ref'] == refs['original_preparation_code_ref']
    old_identity = {'preprocessing_code': {'old.py': 'e'*64}}
    old_meta = {'provenance': {'original': True}}
    writer.save_input('R', {}, [], old_identity, old_meta)
    saved = store.inputs[-1]
    assert saved[3]['preprocessing_code'] == {'old.py': 'e'*64, 'new-source.py': 'a'*64, 'backend.py': 'd'*64}
    assert saved[4]['provenance']['original'] is True and saved[4]['provenance']['prospective_phase_ref'] == refs['prospective_phase_ref']
    assert old_identity == {'preprocessing_code': {'old.py': 'e'*64}} and old_meta == {'provenance': {'original': True}}

    plan = {'sources': [{'source_id': 'S'}], 'requests': [{'source_id': 'S', 'request_id': 'R', 'execution': 'MODEL'}],
            'RGB_groups': {'L': {'source_id': 'S', 'rgb_relative': 'staging/L.npz'}}}
    admission = {'remaining_source_ids': ['S'], '_backend_admission': {'producer_consumers': ['R'], 'cache_root': '/synthetic'}}
    old_exists = Path.exists
    try:
        Path.exists = lambda _path: False
        module.unstarted_source(plan, {'cache_root': '/synthetic'}, admission, 'S')
        Path.exists = lambda path: str(path).endswith('native_measurement_S.json')
        try:
            module.unstarted_source(plan, {'cache_root': '/synthetic'}, admission, 'S')
        except ValueError:
            pass
        else:
            raise AssertionError('Existing successful decode measurement must prevent implicit decode retry')
    finally:
        Path.exists = old_exists
    return {'status': 'PASS_NEW_SYNTHETIC_SOURCE_ADAPTER_AND_FIRST_WRITE_PROVENANCE_ONLY',
            'checks': ['AST_stdlib_no_media_or_model_import', 'frozen_module_globals_unchanged',
                       'unchanged_bytecode_explicit_copied_namespace', 'structural_body_exact_with_first_sidecar',
                       'new_writer_refs_before_first_commit', 'original_preprocessing_map_preserved_plus_actual_code',
                       'existing_measurement_blocks_implicit_retry'],
            'actual_source_decodes': 0, 'processor_encodes': 0, 'model_calls': 0, 'tensor_reads': 0,
            'production_or_backend_admission_tested': False}
