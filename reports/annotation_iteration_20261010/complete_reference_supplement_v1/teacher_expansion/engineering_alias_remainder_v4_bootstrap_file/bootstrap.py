"""Lossless science sentences plus short-line literal routing and unique tail ACK."""
import json
def build(projected_original,index,literal,ack):
 lines=[f"首先本文件已完整读取后，write_to_file TargetFile {index['bootstrap_ack_path']} 一次，内容只能严格复制文件末尾 ACK 六字段。必须先读末尾再写ACK，再读index；无法完整获取末尾、ERROR或截断立即STOP。ACK为有限工程文字供给确认，不是逐帧事实/语义或训练准入。"]
 for line in projected_original.splitlines():
  if line.startswith('本会话literal执行表：'):
   lines.append('本会话literal执行表（完整逐工具参数，禁止猜路径）：')
   for w in literal:
    lines.append('窗口 '+str(w['job_index'])+' sealed_prior_groups='+json.dumps(w['sealed_prior_groups']))
    if w.get('prior_context_AbsolutePath'):lines.append('view_file '+json.dumps({'AbsolutePath':w['prior_context_AbsolutePath']},ensure_ascii=False))
    for g in w['native_groups']:
     lines.append('native group '+str(g['group'])+' 按四slot顺序同response，全4DONE后立即本组write：')
     lines.extend('view_file '+json.dumps(p,ensure_ascii=False) for p in g['view_file'])
     lines.append('write_to_file '+json.dumps(g['write_to_file'],ensure_ascii=False))
    lines.append('view_file clip '+json.dumps(w['clip_view_file'],ensure_ascii=False))
    for batch in w['effective_preview_batches']:
     lines.append('effective 四工具同response：');lines.extend('view_file '+json.dumps(p,ensure_ascii=False) for p in batch)
    lines.append('write_to_file proposal '+json.dumps(w['proposal_write_to_file'],ensure_ascii=False))
  elif line.startswith('读取白名单 '):lines.append('全部读取/自身成功输出自检/写入的完整白名单由本会话冻结index和程序审计严格限定；只能本执行表指定媒体/先ACK指定输出/index及既定事实/提案。不得其他路径，成功输出不得覆盖。')
  else:lines.append(line)
 lines.append('以下是必须先复制写入指定bootstrap_ack.json的全路由摘要；严格仅六字段，不含其它正文：')
 lines.extend(json.dumps(ack,ensure_ascii=False,indent=2).splitlines())
 lines.append('文件末尾独特marker：'+ack['marker'])
 return '\n'.join(lines)+'\n'
