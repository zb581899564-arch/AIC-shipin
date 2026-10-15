现在执行真实TVSum视频逐帧标注小试，保持Gemini 3.8 Flash Medium。只做视觉标注并保存原始结果。

唯一允许读取的目录为当前项目 input/real_tvsum_v1（绝对路径 G:/ai/AIC视频/reports/antigravity_label_probe_20261009/input/real_tvsum_v1）。里面有manifest.json和48张连续原生帧f000.png至f047.png，对应一个真实公开视频的短片段。禁止读取其他目录、验证、原人工标签或旧预测。

只使用内置view_file逐张看PNG、write_to_file保存结果，不用终端、脚本、浏览器、外部API、其他模型或子代理。必须实际查看全部48张，不从首尾插值或凭前帧猜后帧。先读manifest确认每个local_index对应的源frame_index、实际PTS和尺寸；不要声称时间或帧号是自己估计的。

对每张图分别给targetRatioWH=[16,9]和[9,16]推荐构图。bboxes采用源像素[x,y,w]，高度h=w*target_h/target_w；矩形须在640x360源画面内。注意这是推荐构图，兼顾关键动作、人物完整、互动内容和留白，不是绿色矩形测试的主体紧框。宽度可以用小数以保持精确比例，不能为了输出整数而破坏合法性。无明确主体时给可观赏或有信息的场面构图；实在看不清或无法判断才UNKNOWN，框为null。

每帧输出一个对象，字段为local_index、frame_index、pts_seconds、observed_file、visible_content（一句可见事实）、highlight_state（KEEP/NO_HIGHLIGHT/UNKNOWN，判断仅限当前短片段可见视觉证据）、highlight_reason、crops。crops恰好两项，每项targetRatioWH、state（CROP/UNKNOWN）、box_xyw（单个[x,y,w]或null）、reason。不要编造不可见动作/音频；没有精彩动作不强制KEEP，也不把目标不存在等同没有高光。

每6张一批，先逐张查看这6张再直接保存output/real_tvsum_v1/batch_00.json到batch_07.json，每份顶层对象包含frames数组（6项）。输出已落盘不可覆盖或后改。不提供准确率自评，不修正历史测试文件。

全部48帧后保存output/real_tvsum_v1/summary.json：source_id、source_frame_range、observed_files列表、observed_count、output_frame_count、crops_count、highlight_state_counts、crop_unknown_count、clip_events（仅描述本48帧；事件起点source frame、末端end_frame_exclusive）、limitations。说明没有音频且只覆盖这个短片段。最后告诉我实际读取数和落盘文件；如果失败则保存失败记录，不把失败当空标签。
