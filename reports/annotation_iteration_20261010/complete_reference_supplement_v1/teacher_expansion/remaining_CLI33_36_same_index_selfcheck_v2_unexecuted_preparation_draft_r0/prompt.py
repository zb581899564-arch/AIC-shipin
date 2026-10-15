from pathlib import Path
import json

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def build_prompt(a):
    fr=read(a/'freeze.json');idx=read(a/'index.json')
    literal_previews=[dict(job_index=w['job_index'],window_id=w['window_id'],ordered_view_file_arguments=[dict(AbsolutePath=f['path']) for f in w['student_previews']]) for w in idx['windows']]
    prompt=f'''你是独立有限媒体观察教师，只用view_file/write_to_file。禁止terminal/代码/web/目录搜索/其他模型/子代理/旧答案/评分/预测/其他评审，禁止任何未白名单文件。每次会话120分钟cap，无自动重试。
    先view_file { (a/'index.json').as_posix() } 完整读取一次。后续仅在确有必要时可复读这一同路径、同冻结字节的index自查，建议整会话总读取≤5次以节省费用；这只是建议，不是媒体准入次数门。不能改读其他index或文件，不能借自查重复媒体或改变范围；尽量在组完整写出后或预览全8DONE后核对，四图全DONE后仍立即写本组。依windows固定顺序，各窗内容彼此独立，不能跨窗共享证据。每窗按groups0..15固定顺序；每组必须在同一次 agent_response 提交slot0..3顺序的4个独立view_file工具调用（不是只描述计划），每图一次，工具可顺序执行。全4幅工具实际DONE后，下一次响应立即write_to_file该group output_path，然后才下一组。不可在四图之间逐图等待新agent_response，不可把write提前到未全DONE；不得跨组批量读取。只输出严格JSON {{"group":整数,"items":[4条]}}，每条严格字段slot(0..3)、subject(中文可见主体或UNKNOWN)、composition(中文静态构图或UNKNOWN)、subtitle_visible(true/false/"UNKNOWN")、subtitle_text(能清楚读才抄原文，无字幕null，存在辨不清"UNKNOWN")、visible_fact(中文当前单图静态可见事实)。不要frame_id/ordinal/PTS/SHA等身份字段，程序根据冻结slot绑定身份。逐图独立判主体、构图、字幕，不用邻图补猜，不由单图推动作/心理/动机或字幕语言。事实准确简洁，不能为省时省掉任何一图。
    每窗64事实全部写出封存后，view_file本窗clip一次，再在同一次 agent_response 按student_previews固定顺序提交8个独立view_file工具调用（每图一次，工具可顺序执行），全部8图实际DONE后才写proposal。实际学生native processor64帧，教师只是8预览，不称只8学生输入或已逐图看64学生图。视频无音频。
    预览路径必须逐字取本次index.windows[].student_previews[].path，禁止拼接或猜测目录名、替换路径字段。以下是从index逐字提取的每窗8个有序view_file AbsolutePath参数；调用时复制对应整条AbsolutePath，不把student_previews字段名当目录：{json.dumps(literal_previews,ensure_ascii=False)}。每窗只用自己的8条，全8实际DONE后才proposal。任一tool ERROR必须立即停止如实报告，不得把ERROR视为DONE，不得宣称该窗或全部任务成功完成；最终会由真实工具审计区分CLI退出与任务完成。
    随后write_to_file本窗proposal_path一次，完整JSON字段segments、events、student_visibility、limitations。segments须按local seconds完整连续覆盖domain范围，每项严格字段decision(KEEP/NO/UNKNOWN)、start_seconds、end_seconds、reason(具体可见理由，所有NO逐段说明)、fact_support(本窗group/slot对象列表)、start_uncertainty_range_seconds([lower,upper])、end_uncertainty_range_seconds([lower,upper])。保留有明确短时可见亮点的完整短高光，独立事件分别判定；不将整窗叙事、持续说话、常态背景/重复状态或字幕内容自动当高光。不设事件/片段数量配额，不为凑数造事件。可空events，可如实UNKNOWN；边界不足给真实range，不编造精确硬切或失败转空。events每项description、decision、start_seconds、end_seconds、fact_support、boundary_reason。student_visibility说明实际8预览支持和限制，limitations说明不确定。只参考本窗，不猜声音、心理或动机。proposal写出后才开始下一窗。
    每个已成功写出的自身指定output最多view_file核对一次，可省略核对；不得写前读、覆盖或修订成功文件。工具失败立即停止如实报告，禁止重试或猜测填缺图。不称human gold/训练准入。全部固定任务完成自然停。
    本次读取白名单 {json.dumps(fr['read_whitelist'],ensure_ascii=False)}；自身已写核对/写白名单 {json.dumps(fr['write_whitelist'],ensure_ascii=False)}。'''
    return prompt,literal_previews
