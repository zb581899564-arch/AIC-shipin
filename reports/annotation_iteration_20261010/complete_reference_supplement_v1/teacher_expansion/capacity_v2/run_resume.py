from launch import ROOT,read,launch
import json
a=ROOT/'resume_w11';idx=read(a/'index.json');fr=read(a/'freeze.json');w=idx['window']
prompt=f'''工程容量修复精确续接。仅续接本conversation的W11 ({w['window_id']})，原25分钟CLI已真实timeout。本次75分钟cap；不是重问旧成功事实或重新高光意见。明确取消原call00的第二窗任务HT5 W02，禁止开始或查看该窗任何媒体。全局新CLI25/36、logical W11 proposal仍唯一1。
只用view_file/write_to_file，禁止terminal/代码/web/目录搜索/其他模型/子代理/旧评审/旧分数/预测。先view_file { (a/'index.json').as_posix() } 一次。已成功64原PNG/16组facts/clip一次/effective F00,F09,F18三预览全部按冻结原toolstep与SHA继承已有上下文，不重读或重写任何成功PNG/facts/clip/这三preview，也不重新读取原index/manifest/receipt/raw/audit/其他文件。事实仍以原逐图静态facts为准，禁止改写成功事实，不把frame身份当事实，由程序绑定。
未完成的五effective学生预览必须严格依序view_file一次：{json.dumps([f['path'] for f in idx['remaining_previews']],ensure_ascii=False)}。实际学生64，这只是8预览剩5，不冒充逐张看64学生图。
五预览完成后只write_to_file新路径 {w['proposal_path']} 一次，完成完整短高光提案，随后自然停。成功proposal允许view_file核对一次，不覆盖/修订。输出严格JSON字段segments、events、student_visibility、limitations。segments须按local seconds完整连续覆盖[0,{w['domain_local_seconds'][1]}]，每项严格字段decision(KEEP/NO/UNKNOWN)、start_seconds、end_seconds、reason(具体可见依据，全部NO逐段说明)、fact_support(仅本窗group/slot对象列表)、start_uncertainty_range_seconds([lower,upper])、end_uncertainty_range_seconds([lower,upper])。事件独立判定，不设事件或片段数量配额，不将整窗说话/叙事/字幕内容自动当高光；选有明确短时可见亮点的完整短高光。边界不确定如实给range或UNKNOWN，不能编造硬切。events每项description、decision、start_seconds、end_seconds、fact_support、boundary_reason。student_visibility说明实际8预览可辨支持/限制；limitations说明真实不确定。禁止单帧推心理/动机/字幕语言或声音，视频无音频。仅本窗已有视觉事实与上下文作证据，不借另一窗内容。
工具失败立即停止并报告，无自动重试、不失败转空。严格本次读取白名单 {json.dumps(fr['read_whitelist'],ensure_ascii=False)}；自身已写核对/写白名单 {json.dumps(fr['write_whitelist'],ensure_ascii=False)}。不称human gold或训练准入。'''
launch(a,prompt,idx['conversation_id'])
