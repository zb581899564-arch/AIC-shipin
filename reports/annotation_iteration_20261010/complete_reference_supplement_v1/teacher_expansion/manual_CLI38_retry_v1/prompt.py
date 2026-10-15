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
 lines=[f'新前瞻CLI{number}，仅固定{jobs}，7200s/globalcap38/no39；本次用户明确授权一次人工重试，旧37工具前location ERROR及旧36whole REJECT/STOP保持，未验证IP已修复。每窗均完整64native/16事实组/clip一次/8effective/全域proposal，不共享窗口观察。',science,'旧科学段的job17条件只属于旧17会话，本次无17/旧事实移交：当前所有窗口64事实必须本会话真实读图后新写。不得读取旧成功facts/proposal/评分/其它评审或program-only大index。','student在本任务仅指Qwen3-VL-8B学生模型processor的64帧实际输入，教师只直接审8幅effective预览以说明模型可见性支持及限制；绝非学校学生、未成年人或注册身份。student_visibility必须写本窗模型视野，不作人物身份调查。',
 '工程文本路由：本main完整读→本main尾ACK新写；逐窗读header→header尾ACK新写；依header路径第0索引片→其尾ACK→四组native事实；依次其它三片同样供给再四组事实；全部64事实封存后clip→两批各4effective全部DONE→本窗proposal闭合字段模板完整view与尾ACK→proposal，再下一窗。原科学core去掉文本供给后顺序完全保持。','媒体view_file参数只能完整复制literal的AbsolutePath，写入只用给定TargetFile和严格科学JSON；不拼路径、不算ordinal。header同一冻结路径必要只读自检可在其ACK已写后进行，建议总≤5无次数硬门，完整metadata仍验证。main/native索引片只读一次。所有ACK只写一次，不自读。','所有实际读取文本必须<30000B，确切byte/LF/noCR/tail及对应独特ACK核验；metadata总bytes/lines本身不证明正文注意力，未取得完整本片尾ACK立即STOP。','最后当前会话窗口 proposal DONE后立即紧凑JSON最终回答结束，无任何后续工具/日志/history/transcript/网络/账号/凭据/probe/followup。任何ERROR/截断/未完成/缺媒体立即如实STOP，不写缺图事实/空proposal，不以最终SUCCESS替代媒体完成。','以下header路径按固定顺序完整复制；未完成当前窗不得读取下一窗header：']
 for p in headers:lines.append('view_file '+json.dumps({'AbsolutePath':p['path']},ensure_ascii=False))
 return '\n'.join(lines)

def header_body(w,fragments,literal):
 head={k:v for k,v in w.items() if k not in ('groups','native_identity_all64','header_fragment_id','native_fragment_ids','proposal_fragment_id','proposal_template_path')}
 lines=['本窗科学要求完整见已读main；本窗每一事实/语义只参考当前窗。以下header是原index所有非native数组字段，输出路径仅投影新目录。native groups及全部64身份按四片无损分片，禁止读取program-only大index。',compact_records({'window_fields':head}),'四片native索引路径和插入点：']
 for p in fragments:lines.append(compact_records({'part_id':p['part_id'],'before_group':p['before_group'],'before_frame':p['before_native_frame_id'],'view_file':{'AbsolutePath':p['path']}}))
 lines.append('native64事实写完后才使用原clip/effective。8effective全部DONE后，先完整view proposal闭合模板并写尾ACK，再按模板写proposal：');lines.append('view_file '+json.dumps({'AbsolutePath':w['proposal_template_path']},ensure_ascii=False));lines.append(compact_records({'clip_view_file':literal['clip_view_file'],'effective_preview_batches':literal['effective_preview_batches'],'proposal_write_to_file':literal['proposal_write_to_file']}))
 return '\n'.join(lines)

def native_body(w,start,literal):
 return native_schema_notice(w,start)+'\n'+'本片原native身份/literal完整，无新帧/裁剪/clock。先立即写本片ACK，然后按以下四组依次：四幅同response全DONE→下一response立即组事实write；不要跨组读图。禁止复制identity到事实。\n'+compact_records({'job_index':w['job_index'],'window_id':w['window_id'],'groups':w['groups'][start:start+4],'native_identity_all64_slice':w['native_identity_all64'][start*4:(start+4)*4],'literal_native_groups':literal['native_groups'][start:start+4]})


def native_schema_notice(w,start):
 lines=['本片四组事实输出必须各为JSON对象 {"group":本组整数,"items":[四个slot对象]}，禁止输出裸数组，禁止额外顶层字段。四幅本组实际DONE后才写；不要复制下面UNKNOWN类型示例当真实观察，不允许模板替代未看图事实。', '每条且仅有slot/subject/composition/subtitle_visible/subtitle_text/visible_fact；slot整数0..3，中文静态subject/composition/visible_fact或真实UNKNOWN；subtitle_visible true/false/"UNKNOWN"，false配null，辨不清配"UNKNOWN"。']
 for group in range(start,start+4):
  example=dict(group=group,items=[dict(slot=i,subject='<本图静态可见主体或真实UNKNOWN>',composition='<本图静态构图或真实UNKNOWN>',subtitle_visible='UNKNOWN',subtitle_text='UNKNOWN',visible_fact='<本图静态可见事实或真实UNKNOWN>') for i in range(4)])
  lines.append(json.dumps(example,ensure_ascii=False,separators=(',',':')))
 return '\n'.join(lines)

def proposal_example():
 return dict(segments=[dict(decision='<独立判断KEEP/NO/UNKNOWN>',start_seconds='<本段local开始>',end_seconds='<本段local结束>',reason='<本段具体理由，所有NO必须具体说明>',fact_support=[dict(group='<本窗整数0..15>',slot='<整数0..3>')],start_uncertainty_range_seconds=['<lower>','<upper>'],end_uncertainty_range_seconds=['<lower>','<upper>'])],events=[dict(description='<独立可见事件>',decision='<KEEP/NO/UNKNOWN>',start_seconds='<local开始>',end_seconds='<local结束>',fact_support=[dict(group='<本窗整数0..15>',slot='<整数0..3>')],boundary_reason='<真实边界不确定理由>')],student_visibility='<Qwen3-VL-8B processor64帧视野；仅实际审8幅effective预览支持及限制，不是学校学生身份>',limitations=['<当前窗实际不确定与观察限制>'])

def proposal_body(w):
 return '本窗8effective全部实际DONE后完整阅读本片，并立即写本片尾ACK，然后仅一次write本窗proposal。先前全部科学目标原样有效。student仅指Qwen3-VL-8B模型processor64帧输入的可见性；教师仅直接审8effective，不能称看过64学生图，绝不指学校学生或身份注册。\n闭合顶层且仅segments/events/student_visibility/limitations；segments每条且仅decision/start_seconds/end_seconds/reason/fact_support/start_uncertainty_range_seconds/end_uncertainty_range_seconds；events每条且仅description/decision/start_seconds/end_seconds/fact_support/boundary_reason。decision必须KEEP/NO/UNKNOWN。segments连续全域覆盖0至'+str(w['domain_local_seconds'][1])+'，start/end合法local时间；两uncertainty各[lower,upper]在domain内。fact_support每条仅group/slot本窗整数。所有NO逐段具体理由，独立事件分别判断；无事件/片段数量配额，不把整窗叙事/常态状态/持续说话/字幕内容自动当高光。\n以下仅闭合键/类型示意，尖括号不是答案，不得复制占位符、默认标签、时间或事实支持。segments/events数量依实际判断，允许真实UNKNOWN及空events；不凑示例数。\n'+json.dumps(proposal_example(),ensure_ascii=False,indent=1)+'\n最终仅用此原白名单TargetFile：'+json.dumps({'TargetFile':w['proposal_path']},ensure_ascii=False)+'。完成后下一窗；本会话最后窗立即紧凑JSON结束，无后续工具。'
