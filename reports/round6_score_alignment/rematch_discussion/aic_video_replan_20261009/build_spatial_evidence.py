"""Copy only permitted source code needed to challenge spatial proposals."""
from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'rematch_execution' / 'rematch_exec_20261005T1215Z'
SOURCES = [
    ('b_score_aligned_package_v4/field_contract.py', None),
    ('baseline_a_pts_v1/vendor/p2j_core.py', (61, 183)),
    ('b_score_aligned_package_v4/production.py', (140, 198)),
    ('b_score_aligned_package_v4/spatial_baseline.py', (115, 178)),
    ('b_score_aligned_package_v4/spatial_baseline.py', (382, 401)),
]
text = ['# 主控新只读空间代码证据\n\n此处没有运行模型、重新验收旧CPU或修改冻结代码。静态代码并不能证明未检测到的真实镜头边界或主体语义正确。\n']
for relative, bounds in SOURCES:
    path = ROOT / relative
    data = path.read_bytes()
    content = data.decode('utf-8-sig')
    description = '完整文件'
    if bounds:
        start, end = bounds
        content = ''.join(content.splitlines(keepends=True)[start-1:end])
        description = f'原文件L{start}-L{end}，未共享无关CLI/旧fallback路径'
    text += [f'\n## {relative} / {description}\n原文件SHA256 {hashlib.sha256(data).hexdigest()}\n\n```python\n', content, '\n```\n']
text += ['\n静态观察：compose_from_field按group_shots拆分后分别构建anchors并插值；group_shots在显式is_shot_start或ordinal不连续时分割。所以“修复跨已登记镜头插值”须先指出可复现反例，不能把已有分镜机制当尚未实现。production.spatial的实际严格路径只用predict_focus中心，compute_crop_size固定最大合法尺度，parse失败即失败，未调用旧CLI fallback。插值改变不等于新锚点生成，也不等于原空间场exact复用。\n']
(HERE/'spatial-code-evidence.md').write_text(''.join(text), encoding='utf-8')

if __name__ == '__main__':
    print('spatial-code-evidence.md written')
