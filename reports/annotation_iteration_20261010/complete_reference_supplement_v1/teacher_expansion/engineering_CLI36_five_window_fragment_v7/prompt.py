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

def main_body(science,headers):
 lines=['唯一新CLI36，仅固定19/20/21/22/23五窗，7200s/globalcap36；不是重启旧36或重做35媒体。当前五窗原观察均未完成；每窗均完整64native/16事实组/clip一次/8effective/全域proposal，不共享窗口观察。',science,'旧科学段的job17条件只属于旧17会话，本次无17/旧事实移交：所有五窗64事实必须本会话真实读图后新写。不得读取旧成功facts/proposal/评分/其它评审或program-only大index。','工程文本路由：本main完整读→本main尾ACK新写；逐窗读header→header尾ACK新写；依header路径第0索引片→其尾ACK→四组native事实；依次其它三片同样供给再四组事实；全部64事实封存后clip→两批各4effective→proposal，再下一窗。原科学core去掉文本供给后顺序完全保持。','媒体view_file参数只能完整复制literal的AbsolutePath，写入只用给定TargetFile和严格科学JSON；不拼路径、不算ordinal。header同一冻结路径必要只读自检可在其ACK已写后进行，建议总≤5无次数硬门，完整metadata仍验证。main/native索引片只读一次。所有ACK只写一次，不自读。','所有实际读取文本必须<30000B，确切byte/LF/noCR/tail及对应独特ACK核验；metadata总bytes/lines本身不证明正文注意力，未取得完整本片尾ACK立即STOP。','最后job23 proposal DONE后立即紧凑JSON最终回答结束，无任何后续工具/日志/history/transcript/网络/账号/凭据/probe/followup。任何ERROR/截断/未完成/缺媒体立即如实STOP，不写缺图事实/空proposal，不以最终SUCCESS替代媒体完成。','以下header路径按固定顺序完整复制；未完成当前窗不得读取下一窗header：']
 for p in headers:lines.append('view_file '+json.dumps({'AbsolutePath':p['path']},ensure_ascii=False))
 return '\n'.join(lines)

def header_body(w,fragments,literal):
 head={k:v for k,v in w.items() if k not in ('groups','native_identity_all64','header_fragment_id','native_fragment_ids')}
 lines=['本窗科学要求完整见已读main；本窗每一事实/语义只参考当前窗。以下header是原index所有非native数组字段，输出路径仅投影新目录。native groups及全部64身份按四片无损分片，禁止读取program-only大index。',compact_records({'window_fields':head}),'四片native索引路径和插入点：']
 for p in fragments:lines.append(compact_records({'part_id':p['part_id'],'before_group':p['before_group'],'before_frame':p['before_native_frame_id'],'view_file':{'AbsolutePath':p['path']}}))
 lines.append('native64事实写完后才使用下面原clip/effective/proposal literal参数：');lines.append(compact_records({'clip_view_file':literal['clip_view_file'],'effective_preview_batches':literal['effective_preview_batches'],'proposal_write_to_file':literal['proposal_write_to_file']}))
 return '\n'.join(lines)

def native_body(w,start,literal):
 return '本片原native身份/literal完整，无新帧/裁剪/clock。先立即写本片ACK，然后按以下四组依次：四幅同response全DONE→下一response立即组事实write；不要跨组读图。禁止复制identity到事实。\n'+compact_records({'job_index':w['job_index'],'window_id':w['window_id'],'groups':w['groups'][start:start+4],'native_identity_all64_slice':w['native_identity_all64'][start*4:(start+4)*4],'literal_native_groups':literal['native_groups'][start:start+4]})
