"""Write source-isolated native-image labeling queues for the Doubao UI agent."""
from pathlib import Path
from collections import defaultdict
import json
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'corpus.json').read_text(encoding='utf-8'))['sources']
# Interleave categories for an early diverse batch, keep all source memberships fixed.
groups=defaultdict(list)
for r in sorted(m,key=lambda r:(r['split']!='train',r['source_id'])):
    if r['source_id']!='PJrm840pAUI':groups[r['category']].append(r)
order=[]
while any(groups.values()):
    for c in sorted(groups):
        if groups[c]:order.append(groups[c].pop(0))
rows=[]
for r in order:
    sid=r['source_id'];rows.append(dict(source_id=sid,manifest=(ROOT/'input'/sid/'manifest.json').as_posix(),
        image_files=[(ROOT/'input'/sid/f['file']).as_posix() for f in r['frames']],
        draft_output=(ROOT/'raw/doubao'/sid/'draft_01.json').as_posix()))
(ROOT/'doubao_queue.json').write_text(json.dumps(dict(expected_sources=49,frames_per_source=12,ratio_targets_per_source=24,sources=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
task=f'''现在开始余下49条源的批量原图标框，用户已授权标注，继续使用豆包2.1Pro、本地电脑的原生Read/Write工具。
原生Read {(ROOT/'doubao_queue.json').as_posix()}，严格按队列source顺序逐个处理；每条源读manifest并逐张实际Read image_files中的12张原始PNG，只使用本源像素。不读Gemini结果、人类评分、竞赛视频/标签、不运行终端/脚本/代码、浏览器、其他模型、子代理，不训练。
每源把12帧24比例初稿写到指定draft_output，不覆盖任何已存在结果；已有完整输出则回读并跳过。帧身份、pts_seconds、observed_file照manifest真实字段，不从平均fps猜时间、不假设文件名fXX，可能是修复后的native文件名。
JSON格式沿用已完成PJrm840pAUI draft_01.json：source_id、annotator_ui、observed_files、frames。每帧sample_index/frame_index/pts_seconds/observed_file/visible_content/focus_bounds_xyxy，以及crops两条targetRatioWH分别[16,9]和[9,16]、state CROP或UNKNOWN、box_xyw原图整数[x,y,w,h]、reason。h=w*ratioH/ratioW必须精确且坐标不越界。横屏/竖屏都检查核心头脸、手部及操作物体；竖屏无法同时保留主角脸和关键物体时UNKNOWN、box_xyw=null，不要通过凑框声称已保留。
每张至少一条实际可见内容短句，reason简洁，切勿为了省步骤仅凭manifest或缩略图猜框。只有实际Read成功才写observed_files。图像读失败保留具体错误，写本源failure_01.json并继续其它源，失败不能转成空负例。
每源写完回读校验12帧24比例；累计进度写{(ROOT/'raw/doubao/batch_progress.json').as_posix()}（仅进度可更新），含completed_source_ids、failed_source_ids、active_source、observed_frame_count。
持续完成全部49条，避免中途只汇报计划就结束；若应用限制迫使暂停，先写准确进度和停止原因。我会另行把真实裁图交给你复核，初稿不等于合格训练标签。聊天只汇报已实际完成的源数量和错误，不全文重复JSON。'''
(ROOT/'doubao_batch_task.txt').write_text(task+'\n',encoding='utf-8')
print(json.dumps({'queued_sources':len(rows),'queued_frames':len(rows)*12,'first_sources':[r['source_id'] for r in rows[:10]]}))
