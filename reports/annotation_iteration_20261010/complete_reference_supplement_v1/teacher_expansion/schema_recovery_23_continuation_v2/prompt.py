"""Verbatim scientific paragraphs, bounded lossless identity/literal fragments."""
import json

def scientific_text(original):
 lines=original.splitlines();out=[lines[0]]
 line=next(x for x in lines if x.startswith('先view_file本会话index '));out.append('窗口依固定顺序'+line.split('窗口依固定顺序',1)[1])
 for prefix in ('每窗按实际计划groups顺序','本窗全部必要native事实写出封存','随后write_to_file本窗proposal_path一次','成功自身指定输出可在写后'):
  out.append(next(x for x in lines if x.startswith(prefix)))
 return '\n'.join(out)+'\n'

def compact_records(v,indent=0):
 """JSON remains complete; frame/tool parameter records occupy one short line."""
 if isinstance(v,dict) and (set(v)&{'frame_id','AbsolutePath','TargetFile'}):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
 pad=' '*indent
 if isinstance(v,dict):return '{\n'+',\n'.join(' '*(indent+1)+json.dumps(k,ensure_ascii=False)+':'+compact_records(x,indent+1) for k,x in v.items())+'\n'+pad+'}'
 if isinstance(v,list):return '[\n'+',\n'.join(' '*(indent+1)+compact_records(x,indent+1) for x in v)+'\n'+pad+']' if v else '[]'
 return json.dumps(v,ensure_ascii=False)

def piece(body,ack,ack_path):
 return f'本片必须完整view后立即write_to_file TargetFile {ack_path}，内容严格仅尾部六字段ACK。看不到完整尾部、截断或ERROR立即STOP，不补读、不猜marker。ACK仅有限文字/路由供给验证，不是语义或训练通过。\n'+body+'\n必须立即写入的尾部ACK（不得读program-only expected文件）：\n'+json.dumps(ack,ensure_ascii=False,indent=1)+'\n本片唯一尾marker：'+ack['marker']+'\n'

def main_body(science,headers,number,jobs):
 lines=[f'本会话仅CLI{number}固定{jobs}单窗，3600s/globalcap40/no41，无自动retry；原38失败及21验收保持，不读取38半窗facts/proposal。所有64图必须本会话实际供给。',science,'student仅指Qwen3-VL-8B processor64帧模型输入，教师只实际审8effective预览；不是学校学生。原科学要求、闭合事实/提案schema、UNKNOWN/NO理由和独立事件/边界全部有效。','工程路由（以下限制严格收紧科学段的可选自读许可，科学段原字节保持）：main完整view→main尾ACK；header完整view→header尾ACK；每group独立索引片完整view→本片尾ACK→该组四幅native同response全部DONE→下一response立即write该组严格事实对象；16组全部完成后clip一次→两批4effective全部DONE→完整proposal模板view→尾ACK→proposal一次；最终proposal write DONE后立即自然finish紧凑JSON终态，不再任何tools，包括proposal/facts自读、header自查。','每片及所有自读文字<30000B，完整byte/GoLF/tail/noCR/独特ACK严格核验。只能view_file/write_to_file计划literal路径，不拼ordinal/path。main/group/proposal模板各只读一次，header必要同字节自查计数；成功指定facts只可在最终proposal写入之前写后读一次完整自核；proposal绝对不得自读。任一ERROR/截断/schema失败立即STOP，不补空，不把SUCCESS当媒体PASS。','不得读取旧答案/旧半窗/评分/预测/其他review/log/history/network/credentials/probe/终端代码/subagent；科学6段逐字节未变。']
 for p in headers:lines.append('view_file '+json.dumps({'AbsolutePath':p['path']},ensure_ascii=False))
 return '\n'.join(lines)

def header_body(w,fragments,literal):
 head={k:v for k,v in w.items() if k not in ('groups','native_identity_all64','header_fragment_id','native_fragment_ids','proposal_fragment_id','proposal_template_path')}
 lines=['本窗科学要求完整见已读main；本窗每一事实/语义只参考当前窗。以下header是原index所有非native数组字段，输出路径仅投影新目录。native groups及全部64身份按16个单组无损分片，禁止读取program-only大index。',compact_records({'window_fields':head}),'16片每组native索引路径和插入点：']
 for p in fragments:lines.append(compact_records({'part_id':p['part_id'],'before_group':p['before_group'],'before_frame':p['before_native_frame_id'],'view_file':{'AbsolutePath':p['path']}}))
 lines.append('native64事实写完后才使用原clip/effective。8effective全部DONE后，先完整view proposal闭合模板并写尾ACK，再按模板写proposal：');lines.append('view_file '+json.dumps({'AbsolutePath':w['proposal_template_path']},ensure_ascii=False));lines.append(compact_records({'clip_view_file':literal['clip_view_file'],'effective_preview_batches':literal['effective_preview_batches'],'proposal_write_to_file':literal['proposal_write_to_file']}))
 return '\n'.join(lines)

def native_body(w,start,literal):
 example=dict(group=start,items=[dict(slot=i,subject='<实际本图静态主体或真实UNKNOWN>',composition='<实际本图构图或真实UNKNOWN>',subtitle_visible='UNKNOWN',subtitle_text='UNKNOWN',visible_fact='<实际本图静态可见事实或真实UNKNOWN>') for i in range(4)])
 return '本片仅group '+str(start)+'；先完整读本片并写尾ACK，再按literal四幅同response全部DONE，然后下一response立即write唯一事实输出。不得先读下一group。\n事实必须严格JSON对象'+json.dumps(example,ensure_ascii=False,separators=(',',':'))+'；禁止裸list、额外顶层字段或identity。group为本组整数，items仅4个slot0..3；每条且仅slot/subject/composition/subtitle_visible/subtitle_text/visible_fact。subtitle_visible false必须subtitle_text null，true/UNKNOWN配实际literal或UNKNOWN。示例尖括号非标签，禁止复制占位符、默认UNKNOWN替代实读。\n'+compact_records(dict(job_index=w['job_index'],window_id=w['window_id'],groups=[w['groups'][start]],native_identity_all64_slice=w['native_identity_all64'][start*4:(start+1)*4],literal_native_groups=[literal['native_groups'][start]]))

def proposal_example():
 return dict(segments=[dict(decision='<独立判断KEEP/NO/UNKNOWN>',start_seconds='<本段local开始>',end_seconds='<本段local结束>',reason='<本段具体理由，所有NO必须具体说明>',fact_support=[dict(group='<本窗整数0..15>',slot='<整数0..3>')],start_uncertainty_range_seconds=['<lower>','<upper>'],end_uncertainty_range_seconds=['<lower>','<upper>'])],events=[dict(description='<独立可见事件>',decision='<KEEP/NO/UNKNOWN>',start_seconds='<local开始>',end_seconds='<local结束>',fact_support=[dict(group='<本窗整数0..15>',slot='<整数0..3>')],boundary_reason='<真实边界不确定理由>')],student_visibility='<Qwen3-VL-8B processor64帧视野；仅实际审8幅effective预览支持及限制，不是学校学生身份>',limitations=['<当前窗实际不确定与观察限制>'])

def proposal_body(w):
 return '本窗8effective全部实际DONE后完整阅读本片，并立即写本片尾ACK，然后仅一次write本窗proposal。先前全部科学目标原样有效。student仅指Qwen3-VL-8B模型processor64帧输入的可见性；教师仅直接审8effective，不能称看过64学生图，绝不指学校学生或身份注册。\n闭合顶层且仅segments/events/student_visibility/limitations；segments每条且仅decision/start_seconds/end_seconds/reason/fact_support/start_uncertainty_range_seconds/end_uncertainty_range_seconds；events每条且仅description/decision/start_seconds/end_seconds/fact_support/boundary_reason。decision必须KEEP/NO/UNKNOWN。segments连续全域覆盖0至'+str(w['domain_local_seconds'][1])+'，start/end合法local时间；两uncertainty各[lower,upper]在domain内。fact_support每条仅group/slot本窗整数。所有NO逐段具体理由，独立事件分别判断；无事件/片段数量配额，不把整窗叙事/常态状态/持续说话/字幕内容自动当高光。\n以下仅闭合键/类型示意，尖括号不是答案，不得复制占位符、默认标签、时间或事实支持。segments/events数量依实际判断，允许真实UNKNOWN及空events；不凑示例数。\n'+json.dumps(proposal_example(),ensure_ascii=False,indent=1)+'\n最终仅用此原白名单TargetFile：'+json.dumps({'TargetFile':w['proposal_path']},ensure_ascii=False)+'。本会话仅这一窗。最终proposal write DONE后立即自然finish紧凑JSON；禁止proposal自读、facts自读、header自查或任何后续工具。'
