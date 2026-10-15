"""Targeted first-fresh parity checks; no real data/model operation."""
import ast
import importlib.util
from pathlib import Path
import subprocess
import sys

WORK=Path(__file__).resolve().parents[2]
fresh=WORK/'improvement/recall_adapter_role_fresh_v1';positive=WORK/'improvement/recall_adapter_role_confirm_v1'
for p in [*fresh.glob('*.py'),*positive.glob('*.py')]:ast.parse(p.read_text(encoding='utf8'))
for name in ['positive_contract.py','positive_grammar.py','positive_metrics.py']:
    assert (positive/name).read_bytes()==(WORK/'improvement/recall_positive_admission_v1'/name).read_bytes(),'No semantic prompt/grammar/merge change allowed'
sys.path.insert(0,str(fresh))
import fresh_registration as reg
names=['source'+str(i) for i in range(4)]
views=[dict(case_id=s+'.'+role,source_name=s) for role in ['baseline','overlap'] for s in names]
entries=[dict(v) for s in names for v in views if v['source_name']==s]
assert reg.validate_source_grouped_order(dict(unique_views=views,actual_input_count=8),entries,names)==[v['case_id'] for v in entries]
try:reg.validate_source_grouped_order(dict(unique_views=views,actual_input_count=8),views,names)
except ValueError:pass
else:raise AssertionError('Role-major mismatch must not pass')
text=(positive/'positive_runtime.py').read_text(encoding='utf8');tree=ast.parse(text)
defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
infer=ast.get_source_segment(text,defs['infer']);replay=ast.get_source_segment(text,defs['replay'])
assert 'with model.disable_adapter():' in infer and 'ac.validate_restoration' in infer and 'role.role_output' in infer
assert 'ac.restore_frozen_gradients(model)' in infer and 'adapter_enabled_for_all_calls=False' in infer
assert 'ac.validate_restoration' in replay and 'role.role_output(raw, done)' in replay
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['generate','encode','retarget'] for n in ast.walk(defs['replay']))
io=(positive/'positive_io.py').read_text(encoding='utf8')
assert "require(group == 'confirm'" in io and 'REGISTERED_ROLE_POSITIVE_CONFIRM_V1' in io
assert 'BASE_ONLY_POSITIVE_ADMISSION_SAME_INPUT_PAIR' in io and 'PASS_ROLE_DEV_FROZEN_REQUIRES_NEW_UNEXPOSED_CONFIRMATION' in io
chain=(fresh/'fresh_chain.py').read_text(encoding='utf8')
assert chain.index("'first_input_qa'")<chain.index("stage = 'B0';")<chain.index("'B0_replay'")
assert chain.index("'VERIFY_first_input_qa'")<chain.index("stage = 'VERIFY';")
assert "positive_root/'confirm_code'" in chain and "stage_group='confirm'" in chain
assert 'PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40' in chain and 'STOP_ROLE_FRESH_CONFIRM_REJECTED' in chain
print('PASS20py syntax, immutable prompt/grammar/metric bytes, original source-group ordering, exact BASE role, input-before-GPU/output-only, first new confirmation authority')
