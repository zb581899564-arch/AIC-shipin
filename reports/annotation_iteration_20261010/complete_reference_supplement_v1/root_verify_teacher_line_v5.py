"""Root independently checks immutable v5 preparation; does not launch AGY."""
import ast, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
R=Path(__file__).resolve().parent
V5=R/'teacher_expansion/engineering_alias_remainder_v5_line_representation_controller'
V4=V5.parent/'engineering_alias_remainder_v4_bootstrap_file'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
binding=read(V5/'execution_code_binding.json')
for p,s in {**binding['sources'], **binding['frozen_prior_inputs']}.items():
    assert sha(p)==s, p
assert len(binding['frozen_prior_inputs'])==1211
original=(V4/'audit.py').read_text(encoding='utf-8').split('\ndef completed_scope(')[0]+'\n'
assert (V5/'original_engine.py').read_text(encoding='utf-8')==original
a='line_count=len(bootstrap_file.read_bytes().splitlines())'
b="bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().splitlines())"
assert original.count(a)==original.count(b)==1
fixed=original.replace(a,'line_count=len(bootstrap_file.read_bytes().split(bytes([10])))').replace(b,"bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().split(bytes([10])))")
assert (V5/'engine.py').read_text(encoding='utf-8')==fixed
sources=list(V5.glob('*.py')); assert len(sources)==10
for p in sources: ast.parse(p.read_text(encoding='utf-8'))
dry=read(V5/'dry_run_acceptance.json'); independent=read(V5/'independent_preparation_acceptance.json')
assert dry['execution_binding_sha256']==independent['execution_binding_sha256']==sha(V5/'execution_code_binding.json')
assert independent['dry_run_sha256']==sha(V5/'dry_run_acceptance.json')
assert independent['no_plus_minus1_tolerance'] and independent['new_AGY_or_model_calls']==0
assert set(independent['in_memory_negative_cases'])=={'minus1','plus1','wrongbytes','toolERROR','range','wrongACK','wrongorder','mediaERROR'}
assert not any((V4/f'call{n}/request.json').exists() for n in (35,36))
assert not (V5/'registered.json').exists()
ledger=V5.parent/'global_CLI_ledger.jsonl'
assert max(json.loads(s)['global_count'] for s in ledger.read_text(encoding='utf-8').splitlines())==34
out=R/'root_teacher_line_v5_preparation_review.json'
value=dict(status='ROOT_PASS_IMMUTABLE_PREPARATION_PENDING_ACTUAL34_TERMINAL_NOT_START_AUTHORIZATION',
    utc=datetime.now(timezone.utc).isoformat(), execution_binding_sha256=sha(V5/'execution_code_binding.json'),
    dry_run_sha256=sha(V5/'dry_run_acceptance.json'), independent_cpu_preparation_sha256=sha(V5/'independent_preparation_acceptance.json'),
    frozen_input_count=1211, actual_AST_sources=10, only_two_exact_line_representation_substitutions=True,
    root_actually_read_all10_sources_and_protocol=True, old_failures_and_original_dispatch_preserved=True,
    actual_complete34_terminal_and_proof_required_before35=True, no35_36_started=True, no37=True,
    new_AGY_calls=0, new_optimizer_updates=0)
with out.open('x',encoding='utf-8') as f: json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out)),ensure_ascii=False))
