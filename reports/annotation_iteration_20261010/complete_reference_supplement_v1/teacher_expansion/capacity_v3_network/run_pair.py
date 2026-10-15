from launch import ROOT,read,launch
from admission import assert_root_resume_admission
import json,sys
n=int(sys.argv[1]);assert n in range(1,11)
assert_root_resume_admission()
if n>1:assert (ROOT/f'call{n-1:02d}'/'terminal.json').exists(),'Fixed sequential pairs only'
a=ROOT/f'call{n:02d}';fr=read(a/'freeze.json');idx=read(a/'index.json')
prompt=f'''你是独立有限媒体观察教师，只用view_file/write_to_file。禁止terminal/代码/web/目录搜索/其他模型/子代理/旧答案/评分/预测/其他评审，禁止任何未白名单文件。每次会话75分钟cap，无自动重试。
先view_file { (a/'index.json').as_posix() } 一次。依windows固定顺序，各窗内容彼此独立，不能跨窗共享证据。每窗按groups0..15、slot0..3逐张读4原PNG（每图一次），立即write_to_file该group output_path再下一组。只输出严格JSON {{"group":整数,"items":[4条]}}，每条严格字段slot(0..3)、subject(中文可见主体或UNKNOWN)、composition(中文静态构图或UNKNOWN)、subtitle_visible(true/false/"UNKNOWN")、subtitle_text(能清楚读才抄原文，无字幕null，存在辨不清"UNKNOWN")、visible_fact(中文当前单图静态可见事实)。不要frame_id/ordinal/PTS/SHA等身份字段，程序根据冻结slot绑定身份。逐图独立判主体、构图、字幕，不用邻图补猜，不由单图推动作/心理/动机或字幕语言。事实准确简洁，不能为省时省掉任何一图。
每窗64事实全部写出封存后，view_file本窗clip一次，再按student_previews顺序读8effective图一次。实际学生native processor64帧，教师只是8预览，不称只8学生输入或已逐图看64学生图。视频无音频。
随后write_to_file本窗proposal_path一次，完整JSON字段segments、events、student_visibility、limitations。segments须按local seconds完整连续覆盖domain范围，每项严格字段decision(KEEP/NO/UNKNOWN)、start_seconds、end_seconds、reason(具体可见理由，所有NO逐段说明)、fact_support(本窗group/slot对象列表)、start_uncertainty_range_seconds([lower,upper])、end_uncertainty_range_seconds([lower,upper])。保留有明确短时可见亮点的完整短高光，独立事件分别判定；不将整窗叙事、持续说话、常态背景/重复状态或字幕内容自动当高光。不设事件/片段数量配额，不为凑数造事件。可空events，可如实UNKNOWN；边界不足给真实range，不编造精确硬切或失败转空。events每项description、decision、start_seconds、end_seconds、fact_support、boundary_reason。student_visibility说明实际8预览支持和限制，limitations说明不确定。只参考本窗，不猜声音、心理或动机。proposal写出后才开始下一窗。
每个已成功写出的自身指定output最多view_file核对一次，可省略核对；不得写前读、覆盖或修订成功文件。工具失败立即停止如实报告，禁止重试或猜测填缺图。不称human gold/训练准入。全部固定任务完成自然停。
本次读取白名单 {json.dumps(fr['read_whitelist'],ensure_ascii=False)}；自身已写核对/写白名单 {json.dumps(fr['write_whitelist'],ensure_ascii=False)}。'''
launch(a,prompt)
