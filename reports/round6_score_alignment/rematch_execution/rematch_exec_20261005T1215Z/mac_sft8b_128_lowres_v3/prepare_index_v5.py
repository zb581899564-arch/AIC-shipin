from pathlib import Path
import json,shutil,hashlib,datetime as dt,ast
SRC=Path(__file__).resolve().parent;DST=SRC.parent/'mac_sft8b_128_lowres_index_v5'
DST.mkdir(exist_ok=False);(DST/'controller').mkdir()
old=json.loads((SRC/'source_lock.json').read_text())
for name in old['files']:
    target=DST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SRC/name,target)
config=json.loads((DST/'config.json').read_text());config['mps_deepstack_indexing']='FP32_INDEX_ADD_CAST_BACK_BF16'
config['scientific_change']+='; BF16 model retained, DeepStack index addition promoted to FP32 then cast back, no installed library edits'
(DST/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DST/'mps_deepstack.py').write_text('''"""Instance-local MPS backward workaround; no parameter or installed-library edits."""
import types
def deepstack_fp32(self,hidden_states,visual_pos_masks,visual_embeds):
    mask=visual_pos_masks.to(hidden_states.device)
    visual=visual_embeds.to(hidden_states.device,hidden_states.dtype).float()
    work=hidden_states.float()
    local=work[mask,:].clone()+visual
    work[mask,:]=local
    return work.to(hidden_states.dtype)

def install(model,torch):
    target=model.model.language_model
    assert target.__class__.__name__=='Qwen3VLTextModel'
    target._deepstack_process=types.MethodType(deepstack_fp32,target)
    return dict(method='INSTANCE_LOCAL_FP32_INDEX_ADD_CAST_BACK',model_dtype=str(next(model.parameters()).dtype),
        reason='torch2.5.1 MPS IndexBackward index_put accumulate supports Float/Int/Bool only',parameters_added=0)
''')
(DST/'test_deepstack.py').write_text('''import unittest
import torch
from mps_deepstack import deepstack_fp32
def original(x,mask,visual):
    x=x.clone();x[mask,:]=x[mask,:].clone()+visual.to(x.dtype);return x
class Equivalence(unittest.TestCase):
    def test_cpu_bf16_forward_and_backward(self):self.check(torch.bfloat16,'cpu')
    def test_cpu_fp16_forward_and_backward(self):self.check(torch.float16,'cpu')
    def test_mps_bf16_forward_and_backward(self):self.check(torch.bfloat16,'mps')
    def check(self,dtype,device):
        torch.manual_seed(33)
        values=torch.randn(2,19,8).to(dtype);mask=torch.zeros(2,19,dtype=torch.bool);mask[:,1::3]=True
        visual=torch.randn(int(mask.sum()),8).to(dtype)
        a=values.clone().requires_grad_();b=values.to(device).requires_grad_()
        expected=original(a,mask,visual);actual=deepstack_fp32(None,b,mask.to(device),visual.to(device))
        self.assertTrue(torch.equal(expected,actual.detach().cpu()))
        expected.float().square().mean().backward();actual.float().square().mean().backward()
        self.assertTrue(torch.equal(a.grad,b.grad.cpu()))
        self.assertTrue(bool(torch.isfinite(b.grad).all()))
if __name__=='__main__':unittest.main()
''')
path=DST/'train_mac.py';text=path.read_text()
text=text.replace("base.config.use_cache=False", "base.config.use_cache=False\n        from mps_deepstack import install\n        require(config['precision']=='bf16' and config['mps_deepstack_indexing']=='FP32_INDEX_ADD_CAST_BACK_BF16',\n                'DeepStack workaround protocol changed')\n        report['deepstack_workaround']=install(base,torch)")
path.write_text(text)
path=DST/'finish_mac.py';text=path.read_text().replace("environment['PYTORCH_ENABLE_MPS_FALLBACK']='0'", "environment['PYTORCH_ENABLE_MPS_FALLBACK']='0';environment['TORCH_SHOW_CPP_STACKTRACES']='1'");path.write_text(text)
path=DST/'PROTOCOL.md';path.write_text(path.read_text()+'''

## DeepStack 索引精度修正 v5

v4 的FP16同样在IndexBackward失败，0更新，C++堆栈定位PyTorch2.5.1 Indexing.mm:167：index_put的accumulate仅支持Float/Int/Bool。Qwen3VLTextModel._deepstack_process通过布尔索引读取/写回hidden_states，梯度引发该限制。v5保持BF16模型与FP32 LoRA，仅实例级替换此方法：将hidden_states与已按BF16舍入的视觉嵌入转为FP32，进行原索引加法与写回，再转回原dtype；不修改安装库、参数、视觉冻结或其他算子，不脱离MPS计算。CPU BF16/FP16和MPS BF16的小张量测试要求与原CPU实现逐元素前向/梯度一致，真实探针要求完整有限梯度和实际optimizer更新。该修复是显式精度局部变换，完整模型行为还以真实探针验证。v3/v4失败独立保留。首次BF16 forward峰值23.28GiB仅为失败前采样，不承诺完整训练峰值。
''')
names=list(old['files'])+['mps_deepstack.py','test_deepstack.py']
for name in names:
    if name.endswith('.py'):ast.parse((DST/name).read_text(),filename=name)
lock=dict(schema='aic_mac_8b128_lowres_index_source_lock_v5',scope=old['scope'],created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 files={name:hashlib.sha256((DST/name).read_bytes()).hexdigest() for name in names})
(DST/'source_lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(hashlib.sha256((DST/'source_lock.json').read_bytes()).hexdigest())
copy=(SRC.parent/'mac_sft8b_128_lowres_fp16_v4/copy_verified_parent.py').read_text().replace('mac_sft8b_128_lowres_fp16_20261006T0724Z','mac_sft8b_128_lowres_index_20261006T0728Z')
(DST/'copy_verified_parent.py').write_text(copy)
