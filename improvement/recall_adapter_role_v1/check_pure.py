"""Necessary finite-output/activation and phase-order regression, no model/data."""
import ast
import copy
from pathlib import Path
import role_runtime as rt


def reject(call):
    try:call()
    except (ValueError,KeyError,TypeError):return
    raise AssertionError('Malformed activation/output must block')


raw=dict(output_token_ids=[1,2],selected_token_scores=[-1.0,-0.1],generated_score_count=2,output_tokens=2,
    adapter_disabled_layers=[True]*144,actual_model_call=True,actual_physical_parameters=8782459120,
    activated_base_parameters=8767123696,activation_role=rt.ROLE)
assert rt.role_output(raw)==[1,2]
for key,value in [('adapter_disabled_layers',[False]*144),('adapter_disabled_layers',[True]*143),
                  ('actual_physical_parameters',8767123696),('activated_base_parameters',8782459120),
                  ('actual_model_call',False),('selected_token_scores',[float('nan'),-0.1]),('output_tokens',1)]:
    invalid=copy.deepcopy(raw);invalid[key]=value;reject(lambda:rt.role_output(invalid))
root=Path(__file__).parent
for p in root.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
tree=ast.parse((root/'role_runtime.py').read_text(encoding='utf8'))
functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
for stage in ['infer','qa','evaluate','admit']:
    calls=[node for node in ast.walk(functions[stage]) if isinstance(node,ast.Call)]
    assert not any(isinstance(n.func,ast.Attribute) and n.func.attr in ('encode','retarget','decode_window') for n in calls)
qa_calls=[node for node in ast.walk(functions['qa']) if isinstance(node,ast.Call)]
assert not any(isinstance(n.func,ast.Attribute) and n.func.attr=='generate' for n in qa_calls)
infer_source=ast.get_source_segment((root/'role_runtime.py').read_text(encoding='utf8'),functions['infer'])
assert 'with model.disable_adapter():' in infer_source and 'ac.validate_restoration' in infer_source
assert 'ac.restore_frozen_gradients(model)' in infer_source and 'runtime.b_engine.frozen_identity' in infer_source
chain=(root/'role_chain.py').read_text(encoding='utf8')
assert chain.index("child(state,'admit'")<chain.index("stage='UNIQUE_TEN")<chain.index("stage='FIRST_OUTPUT_ONLY_QA'")
print('PASS activation/output rejection; same-input no encode; adopted QA before unique GPU; output-only independent QA; no production')
