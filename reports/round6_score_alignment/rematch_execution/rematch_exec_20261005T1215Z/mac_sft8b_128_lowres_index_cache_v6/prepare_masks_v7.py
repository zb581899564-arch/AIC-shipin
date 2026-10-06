from pathlib import Path
import json,shutil,hashlib,datetime as dt,ast
SRC=Path(__file__).resolve().parent;DST=SRC.parent/'mac_sft8b_128_lowres_mps_v7'
DST.mkdir(exist_ok=False);(DST/'controller').mkdir()
old=json.loads((SRC/'source_lock.json').read_text())
for name in old['files']:
    target=DST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SRC/name,target)
path=DST/'mps_deepstack.py';text=path.read_text()
text=text.replace("target._deepstack_process=types.MethodType(deepstack_fp32,target)",
 "target._deepstack_process=types.MethodType(deepstack_fp32,target)\n    model.model.get_placeholder_mask=types.MethodType(placeholder_mask,model.model)")
text+='''
def placeholder_mask(self,input_ids,inputs_embeds,image_features=None,video_features=None):
    if input_ids is None:raise ValueError('registered training requires explicit input_ids')
    masks=[input_ids==self.config.image_token_id,input_ids==self.config.video_token_id]
    for kind,mask,features in zip(('image','video'),masks,(image_features,video_features)):
        if features is not None:
            count=int(mask.sum().item())
            if features.ndim!=2 or features.shape[0]!=count or features.shape[1]!=inputs_embeds.shape[-1]:
                raise ValueError(f'{kind} token/feature shape mismatch: tokens={count}, feature_shape={tuple(features.shape)}')
    # Equivalent count*hidden check avoids giant noncontiguous boolean index just for numel.
    # Materialize expanded masks for MPS masked_scatter and downstream positional masks.
    return tuple(mask.unsqueeze(-1).expand_as(inputs_embeds).contiguous() for mask in masks)
'''
path.write_text(text)
path=DST/'test_deepstack.py';text=path.read_text().replace('from mps_deepstack import deepstack_fp32','from mps_deepstack import deepstack_fp32,placeholder_mask\nfrom types import SimpleNamespace')
text=text.replace("if __name__=='__main__':unittest.main()",'''class Placeholder(unittest.TestCase):
    def test_cpu_mask_and_strict_count(self):self.check('cpu')
    def test_mps_mask_and_strict_count(self):self.check('mps')
    def check(self,device):
        obj=SimpleNamespace(config=SimpleNamespace(image_token_id=8,video_token_id=9))
        ids=torch.ones(1,2488,dtype=torch.long);ids[:,100:1892]=9
        embeds=torch.zeros(1,2488,4096,dtype=torch.bfloat16)
        features=torch.zeros(1792,4096,dtype=torch.bfloat16)
        masks=placeholder_mask(obj,ids.to(device),embeds.to(device),video_features=features.to(device))
        for mask,token in zip(masks,(8,9)):
            expected=(ids==token).unsqueeze(-1).expand_as(embeds)
            self.assertTrue(mask.is_contiguous());self.assertTrue(torch.equal(mask.cpu(),expected))
            self.assertEqual(int(mask.sum().cpu()),int((ids==token).sum())*4096)
        with self.assertRaises(ValueError):placeholder_mask(obj,ids.to(device),embeds.to(device),video_features=features[:-1].to(device))
if __name__=='__main__':unittest.main()''')
path.write_text(text)
path=DST/'train_mac.py';text=path.read_text().replace("checked.testsRun==3", "checked.testsRun==5").replace("dict(tests=3,failures=0,errors=0", "dict(tests=5,failures=0,errors=0");path.write_text(text)
path=DST/'PROTOCOL.md';path.write_text(path.read_text()+'''

## MPS占位掩码修正 v7

v6在10个完成backward后，forward的原get_placeholder_mask通过inputs_embeds[expanded_boolean_mask].numel检查时报tokens1792/features1792不一致。源代码使用expand得到stride0广播大掩码，MPS动态shape布尔索引产生的大小不可信；输入CPU processor网格与token计数已严格相等，未删除样本。v7实例级替换该辅助检查：显式整数token_count与二维feature的行数、hidden维度逐项相等，不满足即失败；返回与原布尔值完全相同的contiguous扩展掩码供masked_scatter，保留源帧/token/grid合同。只支持登记训练的显式input_ids，其他用法拒绝。增加CPU/MPS大掩码值/数量/连续性及错误feature行数必须拒绝测试，与此前3个前向梯度一致测试合计5项，计入已登记探针耗时，之后仍恢复全部RNG。缓存释放与128帧科学输入不变，完整probe验收之前不进入full。所有旧失败保留。
''')
names=list(old['files'])
for name in names:
    if name.endswith('.py'):ast.parse((DST/name).read_text(),filename=name)
lock=dict(schema='aic_mac_8b128_lowres_mps_source_lock_v7',scope=old['scope'],created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 files={name:hashlib.sha256((DST/name).read_bytes()).hexdigest() for name in names})
(DST/'source_lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
digest=hashlib.sha256((DST/'source_lock.json').read_bytes()).hexdigest();print(digest)
copy=(SRC/'copy_verified_parent.py').read_text().replace('mac_sft8b_128_lowres_index_cache_20261006T0734Z','mac_sft8b_128_lowres_mps_20261006T0740Z')
(DST/'copy_verified_parent.py').write_text(copy)
for name in ['CONTINUE_MAC.md','update_repair_status.py','copy_linux_verified_parent.py','verify_archive.py']:
    text=(SRC/name).read_text().replace('mac_sft8b_128_lowres_index_cache_v6','mac_sft8b_128_lowres_mps_v7').replace('mac_sft8b_128_lowres_index_cache_20261006T0734Z','mac_sft8b_128_lowres_mps_20261006T0740Z').replace('d936c5a76e89f0360010ce3fd29ada8c7e353e4aec360cc145a298605fe21cba',digest).replace('INDEX_CACHE_V6','MPS_V7').replace('v6','v7')
    if name=='update_repair_status.py':text=text.replace("['tests']==3","['tests']==5").replace('逐元素一致3/3','逐元素一致与掩码校验5/5')
    if name=='CONTINUE_MAC.md':text+='\n额外修复：显式token数与feature行数/hidden维度相等检查，contiguous占位掩码；v6旧广播索引大小误判失败保留。\n'
    (DST/name).write_text(text,encoding='utf-8')
