# 可选 M 路线：冻结 CG-DETR 资产准备与 Linux 接入

本文件只补充独立时序候选 `m_specialist` / `m_generic_control` 的资产与接口。先执行主 RUNBOOK 的资源核查、固定提交与现存资产盘点。所有命令在自有 Linux 上运行；本轮公共审计没有下载下述权重、没有执行这些模型，也没有验证选片收益。

**在首次 `bind` 前决定是否准备 M。** 如果直接来源、磁盘或依赖不满足，省略 mapping 的 `specialist`，继续 G/R。不要等 M 阻塞第一包。已绑定的 mapping、asset lock、run root 不可改写；后来补 M 要另建 mapping 和 run root，原有 Qwen/空间调用缓存不能自动跨锁复用，新增成本必须登记，通常不值得在最后窗口这样做。

## 1. 来源和机制固定

| 对象 | 固定身份与用途 |
| --- | --- |
| 原论文 | [Correlation-Guided Query-Dependency Calibration for Video Temporal Grounding](https://arxiv.org/abs/2311.08835v4)，推理时使用其跨模态 moment decoder 和 saliency head；不训练官方来源。 |
| 原论文源码 | [wjun0830/CGDETR](https://github.com/wjun0830/CGDETR)。本次实际加载下面 Lighthouse 发布的 CLIP-only checkpoint 和对应实现，不能混用原仓库其他 checkpoint。 |
| 实际执行源码 | [line/lighthouse](https://github.com/line/lighthouse/tree/3e841d3d662c8440afed514908566fed2d5e82a7)，commit `3e841d3d662c8440afed514908566fed2d5e82a7`，Git tree `271085c23c2619f0336186304e7eeb5be328e4cd`。只导入 `lighthouse.common.cg_detr.build_model`。 |
| CG 权重发布记录 | [Zenodo 固定记录 13363606](https://zenodo.org/records/13363606)，`clip_cg_detr_qvhighlight.ckpt`，发布大小 143.4 MB，发布 MD5 `5a5cfd9cbcdda0c6463fae4b052bf473`。不要点击新版记录、换成 CLIP+SlowFast 或下载整个 1.4 GB 权重集合。 |
| CG 直连 URL | `https://zenodo.org/records/13363606/files/clip_cg_detr_qvhighlight.ckpt?download=1` |
| CLIP 权重 | 优先复用现存原始 OpenAI `ViT-B-32.pt`。固定 SHA256 `40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af`。同架构微调、转换、HF 封装权重不等于这个文件。 |
| CLIP 缺失时的原站 URL | `https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt`，来自 [OpenAI 固定版本模型表](https://github.com/openai/CLIP/blob/dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1/clip/clip.py)。 |
| CLIP Python 实现 | 优先用已正常工作的 OpenAI `clip` 包。确实缺失时可用 [OpenAI/CLIP 固定提交](https://github.com/openai/CLIP/tree/dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1) `dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1`，只安装此小包，不重新安装 torch/torchvision。 |

该路线是冻结的、预训练的跨模态 moment/saliency 模型，不是旧的自训 UMT/I3D 小头、原始 CLIP 相似度或把摘要未选部分当成负例。Qwen BASE 只基于真实概览帧为每源生成一句最多 30 个英文词的自动查询，并承担真实空间定位。`m_generic_control` 复用完全相同的视觉特征，用注册文件中的固定通用查询比较自动查询的贡献。

实现遵循作者训练输入：每 2 秒单元取实际原生中心帧，短边 224、中央裁剪、CLIP RGB 标准化；图像与逐 token 文本特征按 `norm + 1e-5` 归一化。文本不是 pooled embedding。CLIP仍完整编码77上下文，掩码按EOT位置构造（EOT前token 0是内容）。向CG传入至多checkpoint.max_q_l个真实hidden前缀，与作者训练相同；是否截取、原始与实际长度在query_feature_layout中明确记录，缓存profile为CLIP_CAUSAL77_EOT_PADDING_CG_TRAINED_PREFIX_V2。固定 75 单元、步长 60；重叠 saliency 平均；只在前景概率至少 0.5 的预测 moment 内按 saliency 选择，最多占来源**实际时长**的 25%，不强制填满。未预测出前景是合法空结果；模型、输入或 schema 异常是失败。源码中的 `BasePredictor` 有自动下载、75 单元拒绝和计算归一化后仍拼接未归一化图像特征的问题，本项目不调用它。

## 2. 路径与动态容量

以下沿用主 RUNBOOK 已确定的 `FSV1_REPO`、`FSV1_PYTHON`、`FSV1_MAPPING`、`FSV1_WORK`、`FSV1_OUTPUT_PARENT`、`FSV1_SCRATCH`、`FSV1_COMMIT`。这些变量必须是本机真实路径。`FSV1_CLIP` 指向盘点确认的现存原始文件；若确实缺失，指向本节新目录中的 `ViT-B-32.pt`，不得指向需要覆盖的旧文件。

```bash
set -euo pipefail
: "${FSV1_REPO:?主RUNBOOK中的固定仓库路径}"
: "${FSV1_PYTHON:?主RUNBOOK中的现存Python解释器}"
: "${FSV1_MAPPING:?尚未bind的新mapping路径}"
: "${FSV1_OUTPUT_PARENT:?主RUNBOOK已核实容量并用于mapping.workspace_root的现成获准目录}"
export FSV1_OPTIONAL="$FSV1_OUTPUT_PARENT/final_sprint_optional_assets_20261023"
export FSV1_LIGHTHOUSE="$FSV1_OPTIONAL/lighthouse-3e841d3d662c8440afed514908566fed2d5e82a7"
export FSV1_CG="$FSV1_OPTIONAL/clip_cg_detr_qvhighlight.ckpt"
: "${FSV1_CLIP:?填入已盘点的原始ViT-B-32.pt；确实缺失时选择FSV1_OPTIONAL内的新文件}"
export FSV1_CLIP
cd "$FSV1_REPO"
"$FSV1_PYTHON" - <<'PY'
import json, os, pathlib, shutil
work = pathlib.Path(os.environ['FSV1_OUTPUT_PARENT']).resolve(strict=True)
root = pathlib.Path(os.environ['FSV1_OPTIONAL']).resolve()
assert root.is_relative_to(work) and root != work
mapping = json.loads(pathlib.Path(os.environ['FSV1_MAPPING']).read_text())
assert pathlib.Path(mapping['workspace_root']).resolve() == work
assert not (pathlib.Path(mapping['run_root']) / 'sprint_owner.json').exists(), 'STOP: mapping已绑定，不能追加M'
clip = pathlib.Path(os.environ['FSV1_CLIP'])
cg = pathlib.Path(os.environ['FSV1_CG'])
source = pathlib.Path(os.environ['FSV1_LIGHTHOUSE'])
# 这是新产物的规划上界，不是沿用旧0.22GB快照的准入阈值。
# 研究checkout约120MiB；给固定源码及元数据160MiB。首次下载后以du/实际大小更新。
planned = (0 if cg.is_file() else 144_000_000) + (0 if source.is_dir() else 160 << 20)
planned += 0 if clip.is_file() else 400 << 20
reserve = mapping['resources']['disk_reserve_bytes']
output = pathlib.Path(mapping['run_root'])
while not output.exists():
    output = output.parent
if output.stat().st_dev == work.stat().st_dev:
    planned += mapping['resources']['planned_output_bytes']
scratch = pathlib.Path(mapping['resources']['scratch_dir']).resolve(strict=True)
if scratch.stat().st_dev == work.stat().st_dev:
    planned += mapping['resources']['planned_scratch_bytes']
free = shutil.disk_usage(work).free
print(json.dumps({'optional_and_same_disk_planned_bytes':planned,'free_bytes':free,'reserve_bytes':reserve}))
assert free >= planned + reserve, 'STOP: 实际容量不足；不删除基线/模型/Java数据，先选择已有获准工作盘或跳过M'
root.mkdir(parents=True, exist_ok=True)
PY
```

容量核查把同盘的输出和 scratch 一并计算；tmpfs 容量不等于可用物理内存，后续主 preflight 仍检查 `MemAvailable`。这里不创建新的机器、挂载、代理或路由。

## 3. 先验证客户端直连，再获取

仅对本次确实需要下载的公开资产检查原站；现存完整资产采用不要求联网。这段只发送公开站点 HEAD，不下载权重。代理环境、Git URL 重写、代理配置、私网目的地址、CONNECT、重定向、TLS/连接失败或未知 curl 结果均 STOP。不要清空代理变量、改代理配置或换镜像来使检查通过；把具体阻塞交给用户决定，G/R 可以继续。

```bash
"$FSV1_PYTHON" - <<'PY'
import importlib.util, ipaddress, json, os, pathlib, re, socket, subprocess
from urllib.parse import urlsplit
urls = []
if not pathlib.Path(os.environ['FSV1_LIGHTHOUSE']).exists():
    urls.append('https://github.com/line/lighthouse')
if not pathlib.Path(os.environ['FSV1_CG']).is_file():
    urls.append('https://zenodo.org/records/13363606/files/clip_cg_detr_qvhighlight.ckpt?download=1')
if not pathlib.Path(os.environ['FSV1_CLIP']).is_file():
    urls.append('https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt')
clip_source = pathlib.Path(os.environ['FSV1_OPTIONAL'])/'openai-clip-dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1'
if importlib.util.find_spec('clip') is None and not clip_source.exists():
    urls.append('https://github.com/openai/CLIP')
if not urls:
    print(json.dumps({'status':'EXISTING_ASSETS_ONLY_NO_NETWORK_REQUIRED'}))
    raise SystemExit(0)
bad = [k for k,v in os.environ.items() if v and k.lower() in {'http_proxy','https_proxy','all_proxy','ftp_proxy'}]
assert not bad, 'STOP: 当前存在代理变量（仅报告名字）: ' + ','.join(bad)
check = subprocess.run(['git','config','--get-regexp',r'(^http\..*proxy$|^https\..*proxy$|^url\..*insteadof$)'], capture_output=True, text=True)
assert check.returncode == 1, 'STOP: Git代理/URL重写或配置读取异常；不得绕开'
curl_configs = [pathlib.Path.home()/'.curlrc', pathlib.Path(os.environ.get('XDG_CONFIG_HOME', str(pathlib.Path.home()/'.config')))/'curlrc']
if os.environ.get('CURL_HOME'):
    curl_configs.append(pathlib.Path(os.environ['CURL_HOME'])/'.curlrc')
for path in curl_configs:
    if path.is_file():
        assert not re.search(r'(?im)^\s*(?:--)?(?:proxy|preproxy|socks\S*)\b',path.read_text()), 'STOP: curl代理配置需核实'
for url in urls:
    # -q不读curl默认参数；前面已检查代理，绝不靠忽略一个已知代理继续下载。
    result = subprocess.run(['curl','-q','--head','--fail','--silent','--show-error','--noproxy','*',
        '--proto','=https','--max-redirs','0','--connect-timeout','10','--max-time','30',
        '--write-out','\n%{json}\n',url],capture_output=True,text=True)
    assert result.returncode == 0, 'STOP: 公开原站HEAD失败；保持M未执行'
    lines = [line for line in result.stdout.splitlines() if line.startswith('{')]
    assert len(lines) == 1, 'STOP: curl无法提供可验证的连接信息'
    info = json.loads(lines[0]); host = urlsplit(url).hostname
    addresses = {item[4][0] for item in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)}
    remote = info['remote_ip']
    assert info['http_code'] == 200 and info.get('http_connect',0) == 0 and info.get('num_redirects',0) == 0
    assert not info.get('proxy_used',0) and remote in addresses and ipaddress.ip_address(remote).is_global
    assert info['url_effective'] == url, 'STOP: 原站URL发生变化'
    print(json.dumps({'url':url,'status':'DIRECT_CLIENT_HTTPS_HEAD_PASS','remote_ip':remote,
                      'http_code':info['http_code'],'no_proxy_config_changed':True}))
PY
```

成功只证明本机客户端当前对这些原站的直连 HTTPS 请求及校验通过，不代表本公共开发环境已经替训练机验证连通性。若执行端已知网络实际通过未获准中转，则按用户要求停下询问，即使 HEAD 返回 200 也不擅自继续。

### 固定 Lighthouse 源码

原目录存在时验证并采用，不 reset、不覆盖、不修改旧工作区。目录缺失时只获取固定提交。

```bash
if [ ! -e "$FSV1_LIGHTHOUSE" ]; then
  git init "$FSV1_LIGHTHOUSE"
  git -C "$FSV1_LIGHTHOUSE" remote add origin https://github.com/line/lighthouse.git
  GIT_TERMINAL_PROMPT=0 git -C "$FSV1_LIGHTHOUSE" fetch --no-tags --depth=1 origin 3e841d3d662c8440afed514908566fed2d5e82a7
  git -C "$FSV1_LIGHTHOUSE" checkout --detach FETCH_HEAD
fi
"$FSV1_PYTHON" - <<'PY'
import os
from improvement.final_sprint_v1.specialist import _verify_source, AUTHOR_COMMIT, AUTHOR_TREE
print(_verify_source({'path':os.environ['FSV1_LIGHTHOUSE'],'commit':AUTHOR_COMMIT,'tree_sha':AUTHOR_TREE}))
PY
```

若一个失败的 clone 已留下目录，先核对该目录的确切 Git 终态；不要把目录存在当成源码成功，也不要删目录重试。能验证成功的固定 checkout 直接采用；不能验证则本轮 M 保持未执行。

### 固定权重下载、成功采用与原子发布

下段先校验现存文件，只有缺失时下载。失败留下 `.partial`；只有完整校验成功才发布最终名字。重启时若 `.partial` 已经校验成功就直接采用，不重复下载；未完成的 `.partial` 保留现场并 STOP，不静默重启下载或拿它加载模型。

```bash
"$FSV1_PYTHON" - <<'PY'
import hashlib, os, pathlib, subprocess
from improvement.final_sprint_v1.specialist import AUTHOR_CHECKPOINT_URL, AUTHOR_CHECKPOINT_MD5, OPENAI_CLIP_URL, OPENAI_CLIP_SHA256
def digest(path, algorithm):
    value = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):
            value.update(block)
    return value.hexdigest()
for name,url,algorithm,wanted in [('FSV1_CG',AUTHOR_CHECKPOINT_URL,'md5',AUTHOR_CHECKPOINT_MD5),
                                  ('FSV1_CLIP',OPENAI_CLIP_URL,'sha256',OPENAI_CLIP_SHA256)]:
    path = pathlib.Path(os.environ[name]).resolve()
    if path.exists():
        assert path.is_file() and digest(path,algorithm) == wanted, 'STOP: 现存资产身份不同，禁止覆盖'
        print(name,'ADOPTED_EXISTING',path)
        continue
    root = pathlib.Path(os.environ['FSV1_OPTIONAL']).resolve()
    assert path.is_relative_to(root), 'STOP: 新下载必须留在本次专用资产目录'
    partial = path.with_name(path.name+'.partial')
    if partial.exists():
        assert partial.is_file() and digest(partial,algorithm) == wanted, 'STOP: 未完成下载现场存在，先核实终态'
    else:
        subprocess.run(['curl','-q','--fail','--silent','--show-error','--noproxy','*','--proto','=https',
            '--max-redirs','0','--connect-timeout','10','--max-time','600','--output',str(partial),url],check=True)
        assert digest(partial,algorithm) == wanted, 'STOP: 原站权重校验失败，保留现场'
    # 不覆盖最终文件；源和目标处于同目录/文件系统。
    with partial.open('rb') as stream:
        os.fsync(stream.fileno())
    os.link(partial,path)
    partial.unlink()
    print(name,'VERIFIED_PUBLISHED',path,'bytes',path.stat().st_size,'sha256',digest(path,'sha256'))
PY
```

CG 的实际 SHA256 在 Linux 下载完成后计算并写入新 asset lock。MD5 是发布者的交叉校验，不代替运行中的完整 SHA256。加载器在反序列化 CG checkpoint **之前**检查完整资产 SHA 和发布 MD5；CLIP 则检查 OpenAI 发布 SHA。下载命令不发送媒体、标注、tensor 或原始模型回答。

## 4. 复用依赖，禁止安装整个 Lighthouse

先运行导入检查。这不加载模型权重、不做质量筛选。既有 torch/torchvision 必须能共同导入；不能为可选 M 降级 Qwen 正在使用的 torch、transformers 或 numpy。

```bash
"$FSV1_PYTHON" - <<'PY'
import importlib, json, os, sys
for name in ['torch','torchvision','numpy','PIL','scipy','clip','easydict','cv2','av']:
    module = importlib.import_module(name)
    print(name,getattr(module,'__version__','installed'))
sys.path.insert(0,os.environ['FSV1_LIGHTHOUSE'])
from lighthouse.common.cg_detr import build_model
from improvement.final_sprint_v1.specialist import validate_clip_tokens
import clip
validate_clip_tokens(clip.tokenize('A visible action.',context_length=77,truncate=False).tolist())
assert callable(build_model)
print(json.dumps({'status':'OPTIONAL_MODEL_IMPORTS_PASS','model_weights_loaded':False}))
PY
```

实际模型导入只需要既有 PyTorch、NumPy、SciPy 与 OpenAI CLIP 的小依赖；`easydict` 用于作者 checkpoint 的 options 兼容。主程序自身还需 PyAV、OpenCV、Qwen 既有依赖。不要运行 Lighthouse 的 `pip install .` / `pip install -e .` 或其 `setup.py`：它会牵入音频、演示和额外编码器依赖，并限制 transformers/numpy 版本。此路线不加载 SlowFast、PANNs、CLAP、Whisper 或其他模型。

仅当 OpenAI `clip` 包缺失、上述小依赖已存在时，按已经通过的 GitHub 直连检查，获取小源码包并安装到**新专用目录**；本地 wheel 构建不访问网络、不改既有环境包。若 `torchvision` 与当前 torch 本身不兼容，停用 M，不用大规模环境重装抢占冲刺窗口。

```bash
export FSV1_CLIP_SOURCE="$FSV1_OPTIONAL/openai-clip-dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1"
if [ ! -e "$FSV1_CLIP_SOURCE" ]; then
  git init "$FSV1_CLIP_SOURCE"
  git -C "$FSV1_CLIP_SOURCE" remote add origin https://github.com/openai/CLIP.git
  GIT_TERMINAL_PROMPT=0 git -C "$FSV1_CLIP_SOURCE" fetch --no-tags --depth=1 origin dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1
  git -C "$FSV1_CLIP_SOURCE" checkout --detach FETCH_HEAD
fi
test "$(git -C "$FSV1_CLIP_SOURCE" rev-parse HEAD)" = dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1
test -z "$(git -C "$FSV1_CLIP_SOURCE" status --porcelain)"
if [ ! -e "$FSV1_OPTIONAL/python/clip" ]; then
  PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INDEX=1 "$FSV1_PYTHON" -m pip install --no-index --no-deps --no-build-isolation --no-compile --target "$FSV1_OPTIONAL/python" "$FSV1_CLIP_SOURCE"
fi
export PYTHONPATH="$FSV1_OPTIONAL/python${PYTHONPATH:+:$PYTHONPATH}"
```

然后重新运行上面的导入检查。若缺的是小依赖，优先采用现存 wheel；需要新外部下载时，仍须先对其真实原站做相同直连核查，不自动使用配置中的镜像或代理。运行中不会触发模型下载。实际 CLIP 的源码文件、BPE 字典、torch/numpy/Pillow 版本会进入参数收据与逐调用缓存键，跨运行有变化会拒绝错误采用。

## 5. 在首次 bind 前增加精确资产映射

从 bootstrap 的基础 mapping 派生 **另一个新文件** `mapping_with_specialist.json`，加入下面结构，三个 path 使用上述已核实的真实绝对路径；不要添加 TIME/SportCLIP/S1/S0 等无用组件。bootstrap 输出的原 `mapping.json` 保留原样，其 preparation/owner 恢复依赖该文件身份。

```json
{
  "specialist": {
    "source_dir": "/实际工作盘/final_sprint_optional_assets_20261023/lighthouse-3e841d3d662c8440afed514908566fed2d5e82a7",
    "checkpoint": "/实际工作盘/final_sprint_optional_assets_20261023/clip_cg_detr_qvhighlight.ckpt",
    "clip_checkpoint": "/已盘点的真实现存路径/ViT-B-32.pt",
    "published_md5": "5a5cfd9cbcdda0c6463fae4b052bf473"
  }
}
```

可复制的安全写入命令如下：仅从**尚未绑定**的基础 mapping 创建新文件，已有同名目标不一致即停止；不改写原 mapping，不搜索 `latest/vN`。绑定程序随后记录源码完整文件清单、源码 Git commit/tree、文件 bytes/SHA 和发布 MD5。

```bash
export FSV1_MAPPING_WITH_SPECIALIST="$(dirname "$FSV1_MAPPING")/mapping_with_specialist.json"
"$FSV1_PYTHON" - <<'PY'
import json, os, pathlib
from improvement.final_sprint_v1.contracts import atomic_new, ref, strict_load
from improvement.final_sprint_v1.specialist import AUTHOR_CHECKPOINT_MD5
path = pathlib.Path(os.environ['FSV1_MAPPING'])
mapping = json.loads(path.read_text())
assert not (pathlib.Path(mapping['run_root'])/'sprint_owner.json').exists(), 'STOP: 已绑定，禁止改写'
entry = {'source_dir':str(pathlib.Path(os.environ['FSV1_LIGHTHOUSE']).resolve(strict=True)),
         'checkpoint':ref(os.environ['FSV1_CG']), 'clip_checkpoint':ref(os.environ['FSV1_CLIP']),
         'published_md5':AUTHOR_CHECKPOINT_MD5}
assert 'specialist' not in mapping or mapping['specialist'] == entry, 'STOP: 已有不同M资产，须先检查'
mapping['specialist'] = entry
output = pathlib.Path(os.environ['FSV1_MAPPING_WITH_SPECIALIST'])
if output.exists():
    assert strict_load(output) == mapping, 'STOP: 已有不同的可选mapping，不能覆盖'
else:
    atomic_new(output,mapping)
print('OPTIONAL_ASSETS_IN_SEPARATE_UNBOUND_MAPPING',output)
PY
export FSV1_MAPPING="$FSV1_MAPPING_WITH_SPECIALIST"
```

继续主 RUNBOOK 的 `bind`，以及已有监督 wrapper 下的 `preflight`、一次真实 `smoke` 和 `run --candidate m_specialist`。例如 preflight 的实际命令为：

```bash
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli preflight --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --candidate m_specialist --gpu
```

不要绕过主 RUNBOOK 的 wrapper、GPU lease、Java 保护和终态/claim 核对直接后台启动第二个 GPU 作业。

## 6. 参数、输出、恢复与止损

M 的依赖并集是 Qwen3-VL BASE + **一份** CLIP ViT-B/32（图像和文本共享）+ CG-DETR 全部实际参数 + 无权重的 OpenCV 算法。原 BASE 已有精确预期 8,767,123,696；原 CLIP 架构预期 151,277,313，加载时逐张量验证。因此 CG 与其他任何未声明参数最多还剩 81,598,991；这只是预算上界，不是公共环境已经测出的 CG 参数量。Linux 参数收据按实际 materialized 张量与源 checkpoint key 统计，再由外层 `total_parameters` 对完整依赖去重，超过 9,000,000,000 即停止。量化不减参数。

`parameter_receipts()` 没有 `created_at`、PID、内存地址或墙钟字段；独立 runtime 对同一份代码/权重的收据可以被 `write_adopt` 确定性采用。CG 严格加载所有 state keys；CLIP 检查发布文件 SHA、patch/width/tokenizer/投影结构及实际 151,277,313 参数。任何身份不符是工程故障，不能改标签或用其他模型凑包。

| 接口 / 产物 | 契约 |
| --- | --- |
| `plan_cells(source)` | 使用锁定的完整 `normalized_exact_pts` 与 `physical_end_exact`；每个 native ordinal 恰好属于一个单元；样本是实际原生帧。 |
| `encode_source(source, observations)` | 返回 `{rows, features}`；rows 每行有 cell_id、frame、exact PTS、实际像素 SHA、source_id、media SHA；features 是 `[N,512]` 的无损 float32 字节 base64 envelope，带 dtype/shape/bytes/SHA。完整消费 decoder，验证 EOF。 |
| `score_source(source, feature_table, query)` | 自行核实并解码 features，返回 dict，其中 `selected_frames` 是排序、去重的原生整数列表；附每窗 raw logits/spans/saliency、exact duration、query/feature identity 和诊断。runner 直接消费该列表并调用真实空间链。 |
| 逐次 journal | CLIP 图像 batch、CLIP query transformer、CG window 分别 durable；每个真实 compute 收据 `physical_model_forwards=1`。已有成功直接采用，缓存命中不增加新物理调用计数。 |
| 源级终态 | 完整来源另有 SUCCESS_EMPTY / SUCCESS_NONEMPTY；中断或模型异常是失败，不能转成空结果、补默认框或强制非空。 |
| 输出 | `${run_root}/candidates/m_specialist/sources/<video_id>/result.json`、空间证据；最终 `${run_root}/candidates/m_specialist/package/candidate_FINAL_M_SPECIALIST.zip`。以实际 package receipt 的最终 SHA/CRC/成员 SHA 为传输身份。 |

首次真实冒烟只核实这一个真实来源的 CLIP → CG → native frames → Qwen/GrabCut/LK → 合法输出链、实际参数和耗时，不新增代理 F1、五折、盲测或人工标注。若模型源码与现存 torch 不兼容、tokenizer 错误、无可解释的全空/全选崩塌、无法映射 PTS、非法框或参数超限，先定位工程故障，不能出包消耗提交次数。合法个别空来源保留；全包空由包装器拒绝。

固定 M 主路线最多占注册的 4 小时执行预算，通用查询控制最多 2 小时，且服从整个冲刺 18 小时执行上限及至少 4 小时全量验收/传输/算分预留。一次真实 smoke 的全源时间外推包含冷加载且波动较大；只按实际吞吐决定是否完成主 M，不能因为训练/加载成功追加剂量。超过剩余窗口则保留成功日志并切回已经能成包的路线，不恢复旧实验、重复模型调用或扫描阈值。

缓存中的图像与文本隐藏特征使用 **float32 原始字节 base64**，不转 float16、不量化、不截断；解码核实 shape、dtype、精确字节数、SHA 和 finite。若全 426 源实际单元总数为 `N`，CLIP 图像批缓存和源矩阵各存一份，纯数值部分合计约 `2 × N × 512 × 4 × 4/3` 字节，即每单元约 5,462 字节；加原生元数据、常规 claim 与余量，按 `8,192 × N` 字节规划。自动查询每源的 base64 精确长度为 `4 × ceil(77 × 512 × 4 / 3) = 210,264` 字节，426 源约 85.4 MiB；用 `300,000 × 427` 字节覆盖自动查询、一个共享通用查询及其元数据。CG raw 输出、每源选择/空间证据、Qwen journal、重复的源级结果、完整源码 manifest、权重和源码还需另计；这两个公式只是 M 共享特征的保守分项，不是全部路线产物上界。Linux 上真实容量仍由绑定的工程 preflight 核查。

## 7. 本次公共环境实际验证边界

已验证：固定 Lighthouse commit/tree；纯 CPU 的原生 VFR 单元/窗口/预算、合法空与失败分离、CLIP 预处理数值、token shape/身份、缓存 runtime 绑定，以及跨 runtime 参数收据确定性契约。空间端新增了 normalized 1000 边界不会浮点越界的回归检查。

未验证：发布权重内容的本地实际加载、CUDA/显存兼容、现存 Linux OpenAI CLIP/torchvision 导入、真实全源吞吐、真实 GrabCut/LK 冒烟、任何整包质量收益。本文件的命令与工程测试不得写成这些事项已经完成。
