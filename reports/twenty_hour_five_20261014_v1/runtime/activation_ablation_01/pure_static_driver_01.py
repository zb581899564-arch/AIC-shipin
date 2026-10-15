"""Synthetic all144 activation states/inventory/protocol plus static AST only."""
import ast
import base64
import contextlib
import hashlib
import json
import sys
import types

payload = json.loads(base64.b64decode(sys.stdin.buffer.readline()))
sources = payload['code']
trees = {name:ast.parse(code) for name,code in sources.items()}
for name in ('aa_contract','aa_io','run_ablation'):
    module = types.ModuleType(name)
    module.__file__ = '/memory_only_activation_ablation/'+name+'.py'
    sys.modules[name] = module
    exec(compile(sources[name+'.py'],module.__file__,'exec'),module.__dict__)
c,io = sys.modules['aa_contract'],sys.modules['aa_io']
class Parameter:
    requires_grad = False
    def __init__(self,n): self.n = n
    def numel(self): return self.n
class Layer:
    lora_A = {}
    disable_adapters = False
class Model:
    active_adapter = 'default'
    def __init__(self):
        self.layers = [Layer() for _ in range(144)]
        self.params = [('base.weight',Parameter(c.BASE_PARAMETERS)),('layer.lora_A.default.weight',Parameter(c.ADAPTER_PARAMETERS))]
    def named_modules(self): return [(str(index),layer) for index,layer in enumerate(self.layers)]
    def named_parameters(self): return iter(self.params)
    @contextlib.contextmanager
    def disable_adapter(self):
        try:
            for layer in self.layers: layer.disable_adapters = True
            yield
        finally:
            for layer in self.layers: layer.disable_adapters = False
model = Model()
before = c.layer_state(model,False)
inventory = c.parameter_inventory(model)
with model.disable_adapter():
    inside = c.layer_state(model,True,before['layer_names'])
    c.serialized_layer_state(inside,True,before['layer_names'])
after = c.layer_state(model,False,before['layer_names'])
if before != after or inside['activated_parameters'] != c.BASE_PARAMETERS or inventory['actual_physical_parameters'] != c.PHYSICAL_PARAMETERS:
    raise ValueError('Synthetic activation/inventory semantics changed')
try:
    with model.disable_adapter():
        raise RuntimeError('SYNTHETIC_GENERATE_FAILURE')
except RuntimeError:
    pass
c.layer_state(model,False,before['layer_names'])
rejected = []
def reject(name,action):
    try: action()
    except ValueError: rejected.append(name)
    else: raise ValueError('Invalid activation contract accepted: '+name)
with model.disable_adapter():
    model.layers[0].disable_adapters = False
    reject('ONLY_143_DISABLED',lambda:c.layer_state(model,True))
bad = dict(inside,disable_adapters=[True]*143+[False])
reject('FAKE_SERIALIZED_DISABLED_STATE',lambda:c.serialized_layer_state(bad,True))
model.params = model.params[:1]
reject('ADAPTER_UNLOADED_PHYSICAL_COUNT_CHANGED',lambda:c.parameter_inventory(model))
protocol = dict(schema=c.SCHEMA,hypothesis='LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION',
    validation_scope='PAIRED_TWO_CALL_SAME_INPUT_ACTIVATION_DIAGNOSTIC',source_root=str(io.SOURCE),
    max_new_model_calls=2,actual_physical_parameters=c.PHYSICAL_PARAMETERS,activated_base_parameters=c.BASE_PARAMETERS,
    disable_time_adapter_layers=144,optimizer_updates=0,new_input_processor_encodes=0,new_media_decodes=0,
    coarse_and_verify_time_adapter_unchanged=True,old_base_only12_failed_status_and_cost_unchanged=True,
    quality_gate_or_change_based_selection_admitted=False,gpu_job_name='PURE_NEW_ACTIVATION_JOB')
c.protocol(protocol,io.SOURCE)
for key,value in [('max_new_model_calls',3),('quality_gate_or_change_based_selection_admitted',True),
                  ('hypothesis','TIME_ADAPTER_SELECTION_BIAS'),('actual_physical_parameters',c.BASE_PARAMETERS)]:
    reject(key,lambda key=key,value=value:c.protocol(dict(protocol,**{key:value}),io.SOURCE))
infer = next(node for node in trees['run_ablation.py'].body if isinstance(node,ast.FunctionDef) and node.name == 'infer')
replay = next(node for node in trees['run_ablation.py'].body if isinstance(node,ast.FunctionDef) and node.name == 'replay')
calls = [node for node in ast.walk(replay) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)]
if any(node.func.attr in ('encode','baseline_frames','generate') for node in calls):
    raise ValueError('Output-only replay contains a repeated input encode/media/model call')
disable = [node for node in ast.walk(infer) if isinstance(node,ast.With) and any(
    isinstance(item.context_expr,ast.Call) and isinstance(item.context_expr.func,ast.Attribute) and
    item.context_expr.func.attr == 'disable_adapter' for item in node.items)]
if len(disable) != 1 or sum(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr == 'generate'
                            for node in ast.walk(disable[0])) != 1:
    raise ValueError('The one model.generate site is not inside the disable context')
print(json.dumps(dict(status='PASS_ACTIVATION_SYNTHETIC_STATE_PROTOCOL_AND_STATIC_REVIEW_ONLY',syntax_files=len(sources),
    synthetic_all144_before_inside_after_restored=True,synthetic_failure_restores_enabled_state=True,
    physical_parameters_retained=c.PHYSICAL_PARAMETERS,activated_base_parameters=c.BASE_PARAMETERS,
    rejected_cases=rejected,model_generate_site_inside_disable_context=True,output_replay_has_no_input_encode_media_or_model_calls=True,
    actual_admit_calls=0,actual_processor_calls=0,actual_media_decodes=0,actual_model_calls=0,deployed=False,
    code_files={name:dict(bytes=len(code.encode()),sha256=hashlib.sha256(code.encode()).hexdigest()) for name,code in sources.items()})))
