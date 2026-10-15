"""Pure PEFT-like gradient re-enable simulation; no real model or input."""
import ast
import base64
import contextlib
import hashlib
import json
import sys
import types

payload=json.loads(base64.b64decode(sys.stdin.buffer.readline()))
sources=payload['code']
trees={name:ast.parse(code) for name,code in sources.items()}
for name in ('aa_contract','aa_io','run_ablation'):
    module=types.ModuleType(name);module.__file__='/memory_only_remaining_end/'+name+'.py';sys.modules[name]=module
    exec(compile(sources[name+'.py'],module.__file__,'exec'),module.__dict__)
c=sys.modules['aa_contract']
class Param:
    def __init__(self,n):self.n=n;self.requires_grad=False
    def numel(self):return self.n
class Layer:
    lora_A={};disable_adapters=False
class Model:
    active_adapter='default'
    def __init__(self):
        self.layers=[Layer() for _ in range(144)]
        self.params=[('base.weight',Param(c.BASE_PARAMETERS)),('lora_A.default.weight',Param(c.ADAPTER_PARAMETERS))]
    def named_modules(self):return [(str(i),layer) for i,layer in enumerate(self.layers)]
    def named_parameters(self):return iter(self.params)
    def requires_grad_(self,flag):
        for _,parameter in self.params:parameter.requires_grad=flag
        return self
    @contextlib.contextmanager
    def disable_adapter(self):
        try:
            for layer in self.layers:layer.disable_adapters=True
            yield
        finally:
            for layer in self.layers:layer.disable_adapters=False
            self.params[1][1].requires_grad=True  # Real PEFT-like re-enable side effect.
model=Model();before=c.parameter_inventory(model)
with model.disable_adapter():c.layer_state(model,True)
c.layer_state(model,False)
try:c.parameter_inventory(model)
except ValueError:old_failure_reproduced=True
else:raise ValueError('Synthetic old gradient bug did not reproduce')
restore=c.restore_frozen_gradients(model)
assert restore['trainable_tensor_count_before_restore']==1 and restore['trainable_tensor_count_after_restore']==0
assert c.parameter_inventory(model)==before
try:
    try:
        with model.disable_adapter():raise RuntimeError('SYNTHETIC_GENERATION_FAILURE')
    finally:
        exception_restore=c.restore_frozen_gradients(model);c.layer_state(model,False);c.parameter_inventory(model)
except RuntimeError:pass
assert exception_restore['trainable_tensor_count_before_restore']==1
assert c.MAX_CALLS==1 and c.REQUEST_IDS==('SMOKE_ORIGINAL_SCREEN_001.end',) and c.SOURCE_TIME_CALLS==2
infer=next(node for node in trees['run_ablation.py'].body if isinstance(node,ast.FunctionDef) and node.name=='infer')
finals=[node.finalbody for node in ast.walk(infer) if isinstance(node,ast.Try) and node.finalbody]
assert any(isinstance(body[0],ast.Assign) and isinstance(body[0].value,ast.Call) and
           isinstance(body[0].value.func,ast.Attribute) and body[0].value.func.attr=='restore_frozen_gradients' for body in finals)
for fname in ('audit_start','replay'):
    function=next(node for node in trees['run_ablation.py'].body if isinstance(node,ast.FunctionDef) and node.name==fname)
    assert not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and
                   node.func.attr in ('generate','encode','baseline_frames') for node in ast.walk(function))
assert 'paired_two_case_completion=False' in sources['run_ablation.py']
assert "accepted_endpoint_result=None" in sources['run_ablation.py']
print(json.dumps(dict(status='PASS_REMAINING_END_GRADIENT_RESTORE_PURE_FIX_ONLY',syntax_files=3,
    old_activation_restored_but_gradient_bug_reproduced=old_failure_reproduced,
    restore_before_post_state_and_weights=True,normal_and_exception_gradients_restored=True,
    physical_inventory_unchanged=True,remaining_new_model_budget=1,remaining_request_ids=list(c.REQUEST_IDS),
    original_TIME_success_denominator_preserved=2,start_audit_never_adds_accepted=True,no_paired_quality_completion=True,
    actual_admit_calls=0,actual_processor_calls=0,actual_media_decodes=0,actual_model_calls=0,deployed=False,
    code_files={name:dict(bytes=len(code.encode()),sha256=hashlib.sha256(code.encode()).hexdigest()) for name,code in sources.items()})))
