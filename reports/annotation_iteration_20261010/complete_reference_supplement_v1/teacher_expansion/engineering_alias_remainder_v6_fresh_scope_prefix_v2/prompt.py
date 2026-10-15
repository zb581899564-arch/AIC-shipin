"""Preserve original science; only full-window routing and terminal engineering change."""
import json

def build(original,index,literal,ack):
 lines=[f"首先完整view本文件后，write_to_file TargetFile {index['bootstrap_ack_path']} 一次，严格仅文件末尾ACK六字段。必须实际读尾marker再写ACK，随后index；截断/ERROR/不能获取ACK立即STOP。ACK仅有限文字与路由供给验证，不是科学/语义/训练验收。"]
 for line in original.splitlines():
  if line.startswith('本会话literal执行表：'):
   lines.append('本会话literal执行表：逐字复制参数，禁止猜路径。')
   for w in literal:
    lines.append('窗口 '+str(w['job_index'])+'；全部16组64native事实，不含旧事实移交。')
    for g in w['native_groups']:
     lines.append('native group '+str(g['group'])+' 四slot同response顺序工具，全4DONE后立即下一response写：')
     lines.extend('view_file '+json.dumps(p,ensure_ascii=False) for p in g['view_file'])
     lines.append('write_to_file '+json.dumps(g['write_to_file'],ensure_ascii=False))
    lines.append('view_file clip '+json.dumps(w['clip_view_file'],ensure_ascii=False))
    for batch in w['effective_preview_batches']:
     lines.append('effective 四个view同response顺序：');lines.extend('view_file '+json.dumps(p,ensure_ascii=False) for p in batch)
    lines.append('write_to_file proposal '+json.dumps(w['proposal_write_to_file'],ensure_ascii=False))
  elif line.startswith('仅job17为明确成功观察移交：'):
   lines.append('本会话各窗均完整16组64原native PNG和64新事实，逐窗独立，不含任何旧事实/proposal/其它评审移交。')
  elif line.startswith('读取白名单 '):
   lines.append('完整路径白名单由冻结index/程序审计执法：只许本文件一次、指定ACK一次新写、同index必要只读自检、literal媒体、指定新事实/提案。成功自身输出只可写后自检一次，不覆盖。')
  else:
   line=line.replace('（job17旧32+新32，其余新64）','（本会话各窗新64）').replace('与job17观察移交','')
   lines.append(line)
 lines.append('最后一个固定窗口proposal写入DONE后，立即用一个紧凑JSON最终回答结束（fixed_job_indices与completed即可）。不得再调用任何工具，也不得读取内部日志/历史/transcript/网络/凭据/探测文件，不发后续请求。发生真实ERROR立即STOP，不补写空事实/提案，不宣称SUCCESS。')
 lines.append('必须先复制到指定bootstrap_ack.json的完整六字段尾部摘要：')
 lines.extend(json.dumps(ack,ensure_ascii=False,indent=2).splitlines())
 lines.append('文件末尾唯一marker：'+ack['marker'])
 return '\n'.join(lines)+'\n'
