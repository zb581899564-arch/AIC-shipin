      "local_seconds_exact": "79979/3000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头口述讲话。"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 9804,
      "local_seconds_exact": "67817/2500",
      "observed": true,
      "visible_fact": "中年男子持续讲话，眼神微动。"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 9818,
      "local_seconds_exact": "413909/15000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 9832,
      "local_seconds_exact": "105229/3750",
      "observed": true,
      "visible_fact": "中年男子持续讲话，口型变动。"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 9847,
      "local_seconds_exact": "856847/30000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话，面部正面特写。"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 9861,
      "local_seconds_exact": "290287/10000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，发音口型微张。"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 9875,
      "local_seconds_exact": "7079/240",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 9890,
      "local_seconds_exact": "89989/3000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话至本窗口结束，背景保持木栅栏与房屋。"
    }
  ],
  "effective_view_observations": [
    {
      "frame_id": "F00",
      "local_seconds_exact": "62/1875",
      "observed": true,
      "visible_fact": "手部按在轮胎轮毂中心气门嘴位置的特写。",
      "student_visibility_limitations": "手部与轮毂的大体几何轮廓可见，但轮胎橡胶表面的细微模具文字规格模糊不清，不可作为高分辨率可辨识特征传授给学生模型。"
    },
    {
      "frame_id": "F08",
      "local_seconds_exact": "57553/15000",
      "observed": true,
      "visible_fact": "俯视视角展示静止的车轮、白色喷雾瓶、扳手及红色工具箱。",
      "student_visibility_limitations": "轮胎主体、喷雾瓶身和工具箱外轮廓可辨，但扳手开口结构及工具箱内部细节存在明显的像素下采样模糊。"
    },
    {
      "frame_id": "F16",
      "local_seconds_exact": "11461/1500",
      "observed": true,
      "visible_fact": "俯视全景持续展示静止车轮及周边工具。",
      "student_visibility_limitations": "大物块位置和色彩分界清晰，水泥地微小颗粒与工具反光边缘的高频纹理退化。"
    },
    {
      "frame_id": "F24",
      "local_seconds_exact": "171667/15000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话的特写镜头起始。",
      "student_visibility_limitations": "人脸五官与胡子外形可辨，但皮肤皱纹细节及背景木栅栏纹理因压缩反排而平滑化。"
    },
    {
      "frame_id": "F32",
      "local_seconds_exact": "57181/3750",
      "observed": true,
      "visible_fact": "中年男子面向镜头持续口述特写。",
      "student_visibility_limitations": "人脸面部表情及张口姿态可见，远处房屋窗框和树木枝条的高频细节模糊。"
    },
    {
      "frame_id": "F40",
      "local_seconds_exact": "285781/15000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话人像特写。",
      "student_visibility_limitations": "人头轮廓和嘴唇动作可辨，眼神光和胡须根部精细纹理不可精确识别。"
    },
    {
      "frame_id": "F48",
      "local_seconds_exact": "171419/7500",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头口述特写。",
      "student_visibility_limitations": "主要人像动作可跟踪，微细面部阴影渐变受 patch 逆变换伪影影响有所损失。"
    },
    {
      "frame_id": "F56",
      "local_seconds_exact": "79979/3000",
      "observed": true,
      "visible_fact": "中年男子面向镜头持续口述特写至后半段。",
      "student_visibility_limitations": "整体人脸形态稳定可辨，背景铁丝网与木栅栏细线细节模糊。"
    }
  ],
  "events": [
    {
      "event_id": "event_01",
      "visible_facts": "手部在轮胎轮毂中心位置对气门嘴进行按压检查，近距离特写展示气门嘴安装及固定状态。",
      "highlight_reason": "关键动作与核心组件安装细节特写展示，直接展示轮胎气门嘴安装后的检查与状态验证，信息密度高，属于清晰的主题操作与关键部件结果展示。",
      "evidence_frame_ids": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04"
      ],
      "proposed_local_seconds": [
        0.0,
        2.169
      ],
      "start_uncertainty_range": [
        0.0,
        0.033067
      ],
      "end_uncertainty_range": [
        1.934967,
        2.4021
      ],
      "boundary_inside_frame_ids": [
        "F00",
        "F04"
      ],
      "boundary_outside_frame_ids": [
        "F05"
      ],
      "limitations": "特写动作在窗口起始处已在进行中；切出点位于 F04 与 F05 之间，存在约 0.467 秒的稀疏抽帧采样间隙。"
    },
    {
      "event_id": "event_02",
      "visible_facts": "组装好的越野车轮平放在水泥地面上，右侧陈列配套检漏喷雾瓶、活动扳手及红色工具箱，呈俯视完整静置展示。",
      "highlight_reason": "清晰的主题成果展示（安装完成的轮胎车轮）与关联检修工具全景，符合保留必要成果展示原则；且未跨无关镜头强行合并。",
      "evidence_frame_ids": [
        "F05",
        "F06",
        "F07",
        "F08",
        "F09",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
        "F22",
        "F23"
      ],
      "proposed_local_seconds": [
        2.169,
        11.194
      ],
      "start_uncertainty_range": [
        1.934967,
        2.4021
      ],
      "end_uncertainty_range": [
        10.943967,
        11.444467
      ],
      "boundary_inside_frame_ids": [
        "F05",
        "F23"
      ],
      "boundary_outside_frame_ids": [
        "F04",
        "F24"
      ],
      "limitations": "画面长达约 8.8 秒完全静止无动作位移，短视频二次精剪中可根据节奏需要压缩时长；起止边界各有约 0.5 秒采样间隙不确定度。"
    }
  ],
  "window_coverage": [
    {
      "start": 0.0,
      "end": 2.169,
      "label": "KEEP",
      "visible_basis": "手部按压检查轮毂中央气门嘴的特写，明确展示关键部件安装状态与检查动作。",
      "evidence_frame_ids": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04"
      ]
    },
    {
      "start": 2.169,
      "end": 11.194,
      "label": "KEEP",
      "visible_basis": "组装完成的越野轮胎及配套检修工具（白色喷雾瓶、活动扳手、红色工具箱）俯视静置全景展示，为清晰的主题成果及装备展示。",
      "evidence_frame_ids": [
        "F05",
        "F06",
        "F07",
        "F08",
        "F09",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
        "F22",
        "F23"
      ]
    },
    {
      "start": 11.194,
      "end": 30.0,
      "label": "NO",
      "visible_basis": "中年男子面向镜头讲话人像特写（Talking head），脱离核心操作对象（轮胎、工具），无展示性动作或关键视觉变化，且无声音解说配合，视觉高光价值低，在短视频剪辑中明确排除。",
      "evidence_frame_ids": [
        "F24",
        "F25",
        "F26",
        "F27",
        "F28",
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40",
        "F41",
        "F42",
        "F43",
        "F44",
        "F45",
        "F46",
        "F47",
        "F48",
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "consequential_unknowns": [],
  "explicit_no_highlight": [
    {
      "segment_local_seconds": [
        11.194,
        30.0
      ],
      "reason": "中年男子面向镜头的长时段口述人像（Talking head），画面完全脱离主题修复实物（轮胎、轮毂、工具），缺乏展示性动作与视觉高光信息，无音频伴随，在短视频编辑中建议排除。",
      "evidence_frame_ids": [
        "F24",
        "F25",
        "F26",
        "F27",
        "F28",
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40",
        "F41",
        "F42",
        "F43",
        "F44",
        "F45",
        "F46",
        "F47",
        "F48",
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "student_visibility_limitations": [
    "学生有效视图（544x352）经过 patch 反排与反归一化重构，相比原生 RGB（540x360）在高频纹理和边缘清晰度上存在明显退化。",
    "原生图像中轮胎橡胶表面的细微模具规格字样在学生有效视图中完全不可辨认，不可假定模型在有效输入下具备对超细粒度文字细节的学习能力。",
    "扳手开口边缘结构、工具箱内杂物以及讲话人人脸细微皱纹、胡须边缘在学生有效视图中受下采样平滑影响，判别能力受限。"
  ],
  "limitations": [
    "本提案基于离散稀疏抽样的 64 帧原生画面与 8 帧学生有效视图，平均采样间隔约为 0.47 秒，镜头切换点存在 ±0.25 秒的不确定性范围。",
    "编码视频不含音频轨道（no audio），所有分析均严格基于直接可见事实，无法获知口述语音内容。",
    "此任务只产生有限观察下完整窗口银标提案，绝非金标真值，不授予训练资格。"
  ],
  "training_admitted": false
}


## 完整新增公开证据：audit.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\02_AwmHb44_ouw_W10\teacher_attempt01_http1\audit.json
字节：12255；SHA256：9ee6827ddb8fbeb3847351ceb5b074525868604a6a8421e02cbfa1b09c4f1b88

{
  "status": "OBSERVATION_AUDIT_ONLY_NOT_SILVER_ADMISSION",
  "window_id": "AwmHb44_ouw:SLOT6:10",
  "actual_model": "gemini-3.8-flash-high",
  "actual_result_status": "SUCCESS",
  "actual_result_error": null,
  "actual_result_usage": {
    "input_tokens": 440055,
    "output_tokens": 37669,
    "thinking_tokens": 20422,
    "cache_read_tokens": 1669535,
    "total_tokens": 477724
  },
  "original_pngs_delivered": 64,
  "original_pngs_expected": 64,
  "missing_original": [],
  "effective_pngs_delivered": 8,
  "effective_pngs_expected": 8,
  "native_video_delivered": true,
  "actual_completed_tool_count": 78,
  "read_counts": {
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\manifest.json": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\receipt.json": 3,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\clip.mp4": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F00_O008992.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F01_O009006.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F02_O009020.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F03_O009034.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F04_O009049.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F05_O009063.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F06_O009077.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F07_O009091.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F08_O009106.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F09_O009120.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F10_O009134.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F11_O009148.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F12_O009163.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F13_O009177.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F14_O009191.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F15_O009205.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F16_O009220.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F17_O009234.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F18_O009248.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F19_O009262.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F20_O009277.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F21_O009291.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F22_O009305.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F23_O009319.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F24_O009334.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F25_O009348.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F26_O009362.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F27_O009376.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F28_O009391.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F29_O009405.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F30_O009419.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F31_O009433.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F32_O009448.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F33_O009462.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F34_O009476.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F35_O009490.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F36_O009505.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F37_O009519.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F38_O009533.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F39_O009547.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F40_O009562.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F41_O009576.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F42_O009590.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F43_O009604.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F44_O009619.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F45_O009633.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F46_O009647.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F47_O009661.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F48_O009676.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F49_O009690.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F50_O009704.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F51_O009718.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F52_O009733.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F53_O009747.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F54_O009761.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F55_O009775.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F56_O009790.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F57_O009804.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F58_O009818.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F59_O009832.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F60_O009847.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F61_O009861.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F62_O009875.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F63_O009890.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F00_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F08_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F16_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F24_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F32_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F40_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F48_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F56_student.png": 1
  },
  "tool_issues": [],
  "proposal_geometry_identity_issues": [],
  "proposal_events": 2,
  "consequential_unknown_coverage": false,
  "proposal_sha256": "bf26a73380aeb0a8fe1acdea44f11f16de034832100cab558851437c93fd4c17",
  "stream_sha256": "cb09e9643ffc3b78d5ad6553bf3a2e528967424d4ffb2fda74de2fedce82a6c7",
  "request_sha256": "18f0ddd747f60ac4a716549dd101d102cbaee46af1f6789eb8b8fa1ed0e4d4e1",
  "all_floor64_delivered_not_attention_or_full_native_proof": true,
  "training_admitted": false,
  "new_optimizer_updates": 0
}

## 完整新增公开证据：terminal.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\02_AwmHb44_ouw_W10\teacher_attempt01_http1\terminal.json
字节：266；SHA256：948c3d797e4717ec14b4b9b047ba9da4535b020b006dc32c962e1e0e88467511

{
  "started_utc": "2026-10-10T06:09:02.542122+00:00",
  "finished_utc": "2026-10-10T06:16:25.372159+00:00",
  "exit_code": 0,
  "elapsed_seconds": 442.82800000000043,
  "proposal_exists": true,
  "exit_zero_not_success": true,
  "new_optimizer_updates": 0
}

## 完整新增公开证据：02_AwmHb44_ouw_W10.independent_initial_blind_v1.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\02_AwmHb44_ouw_W10.independent_initial_blind_v1.json
字节：63012；SHA256：a8b6e30dcc4fdd79fe4ef53bc6b2f7605ae06616d62aa9c7faaad9c56e46904d

{
  "schema": "independent_initial_blind_review_v1",
  "review_utc": "2026-10-10 05:47:39 UTC",
  "reviewer": "独立执行Agent",
  "review_kind": "INITIAL_SAMPLED_NATIVE_PNG_BLIND_REVIEW",
  "window_id": "AwmHb44_ouw:SLOT6:10",
  "source_id": "AwmHb44_ouw",
  "source_identity_manifest_declared": {
    "source_sha256": "82ecca1de0363253060bb3c19e2f5dbd4080bfc0cd790db23c3e73ffd76a602f",
    "source_total_frames": 10597,
    "source_file_independently_read_or_hashed": false
  },
  "manifest": {
    "path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/observations/02_AwmHb44_ouw_W10/manifest.json",
    "sha256_as_initial_read": "838b7362c8061f824e1ccc79059ba3406185eff9143ef2ec303e9f3bef8c0a52",
    "plan_sha256": "09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22",
    "domain_global_seconds_exact": [
      "300",
      "330"
    ],
    "clip_encoding_declared": "all native frames; exact PTS deltas; unchanged geometry; libx264 crf18 yuv420p lossy pixels; no audio"
  },
  "blind_attestation": {
    "teacher_content_received": false,
    "teacher_files_read": false,
    "old_labels_read": false,
    "human_scores_read": false,
    "model_predictions_read": false,
    "discussion_or_context_files_read": false,
    "other_project_files_read": false,
    "network_or_model_or_gpu_used": false,
    "overview_images_used": false,
    "native_clock_read": false,
    "clip_or_audio_read": false,
    "source_evidence_modified": false
  },
  "visibility": {
    "sampled_original_pngs_observed": 64,
    "all_floor64_pngs_actual_view_image_read": true,
    "view_batches": 8,
    "view_batch_size": 8,
    "student_processor_visibility_verified": false,
    "training_admitted": false,
    "full_native_frames_observed": false,
    "student_effective_views": "NOT_OBSERVED_IN_THIS_REVIEW",
    "not_gold_label": true
  },
  "bindings": {
    "all_64_png_files_exist": true,
    "all_64_png_sha256_match_manifest": true,
    "rgb_pixel_sha256_recomputed": false,
    "actual_source_video_PTS_independently_verified": false,
    "PTS_binding": "逐帧记录manifest source_ordinal、global/local exact PTS、PNG路径与实际文件SHA；没有读取源视频或native_clock做二次时钟验证"
  },
  "time_contract": {
    "units": "global source seconds",
    "interval_convention": "[start,end)，最后一段至声明窗口末端；采样锚点处边界仅为初始编辑建议，不是逐native帧切点",
    "K_NO_U_mutually_exclusive": true,
    "declared_window_fully_partitioned": true,
    "unmentioned_time_not_implicitly_NO": true,
    "sample_max_gap_seconds_approx": 0.500500000000045,
    "sampling_residual_risk": "仅观察floor64样本，短瞬时动作、遮挡、镜头切点与非采样变化仍可能漏掉。稳定同镜头重复间隙未机械标UNKNOWN；已识别能改变标签的切点、失焦与讲述意义列具体U。边界须后续更密帧证据核验。"
  },
  "segments": [
    {
      "segment_id": "S01",
      "label": "K",
      "global_seconds_exact": [
        "300",
        "9058049/30000"
      ],
      "title": "手与轮圈内侧小凸点的操作细节",
      "visual_reason_or_unknown": "近距离展示手指与轮圈内侧的接触关系和构造细节，有技术过程镜头价值；具体用途未确认。",
      "evidence_frames": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04"
      ]
    },
    {
      "segment_id": "S02",
      "label": "U",
      "global_seconds_exact": [
        "9058049/30000",
        "3024021/10000"
      ],
      "title": "操作近景到地面轮胎全景的切点",
      "visual_reason_or_unknown": "手消失并换全景，切点未知；接触后的机械结果未见。",
      "evidence_frames": [
        "F04",
        "F05"
      ]
    },
    {
      "segment_id": "S03",
      "label": "K",
      "global_seconds_exact": [
        "3024021/10000",
        "38038/125"
      ],
      "title": "轮胎、轮圈与相邻工具的全景",
      "visual_reason_or_unknown": "轮胎平放、轮圈朝上、白喷瓶和可调扳手的位置清楚，可作短建立/状态镜头；不声称修好或工具已使用。",
      "evidence_frames": [
        "F05",
        "F06",
        "F07",
        "F08",
        "F09"
      ]
    },
    {
      "segment_id": "S04",
      "label": "NO",
      "global_seconds_exact": [
        "38038/125",
        "9328319/30000"
      ],
      "title": "同一轮胎工具布局的重复持留",
      "visual_reason_or_unknown": "物品静态关系已建立，后续样本仅轻微机位变化，未见操作或新结果。",
      "evidence_frames": [
        "F09",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
        "F22",
        "F23"
      ]
    },
    {
      "segment_id": "S05",
      "label": "U",
      "global_seconds_exact": [
        "9328319/30000",
        "4671667/15000"
      ],
      "title": "工具布局到人物面部镜头的切点",
      "visual_reason_or_unknown": "主体变化，切点未知。",
      "evidence_frames": [
        "F23",
        "F24"
      ]
    },
    {
      "segment_id": "S06",
      "label": "U",
      "global_seconds_exact": [
        "4671667/15000",
        "330"
      ],
      "title": "连续人物近景的讲述意义",
      "visual_reason_or_unknown": "嘴型持续变化，可能有与过程相关的关键说明；没有音频/转录，不能确认说了什么，也不能默认全部人物近景为NO。视觉上未见手势、工具操作或新结果。",
      "evidence_frames": [
        "F24",
        "F25",
        "F26",
        "F27",
        "F28",
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40",
        "F41",
        "F42",
        "F43",
        "F44",
        "F45",
        "F46",
        "F47",
        "F48",
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "keep_events": [
    {
      "segment_id": "S01",
      "label": "K",
      "global_seconds_exact": [
        "300",
        "9058049/30000"
      ],
      "title": "手与轮圈内侧小凸点的操作细节",
      "visual_reason_or_unknown": "近距离展示手指与轮圈内侧的接触关系和构造细节，有技术过程镜头价值；具体用途未确认。",
      "evidence_frames": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04"
      ]
    },
    {
      "segment_id": "S03",
      "label": "K",
      "global_seconds_exact": [
        "3024021/10000",
        "38038/125"
      ],
      "title": "轮胎、轮圈与相邻工具的全景",
      "visual_reason_or_unknown": "轮胎平放、轮圈朝上、白喷瓶和可调扳手的位置清楚，可作短建立/状态镜头；不声称修好或工具已使用。",
      "evidence_frames": [
        "F05",
        "F06",
        "F07",
        "F08",
        "F09"
      ]
    }
  ],
  "explicit_no_intervals": [
    {
      "segment_id": "S04",
      "label": "NO",
      "global_seconds_exact": [
        "38038/125",
        "9328319/30000"
      ],
      "title": "同一轮胎工具布局的重复持留",
      "visual_reason_or_unknown": "物品静态关系已建立，后续样本仅轻微机位变化，未见操作或新结果。",
      "evidence_frames": [
        "F09",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
        "F22",
        "F23"
      ]
    }
  ],
  "unknown_intervals": [
    {
      "segment_id": "S02",
      "label": "U",
      "global_seconds_exact": [
        "9058049/30000",
        "3024021/10000"
      ],
      "title": "操作近景到地面轮胎全景的切点",
      "visual_reason_or_unknown": "手消失并换全景，切点未知；接触后的机械结果未见。",
      "evidence_frames": [
        "F04",
        "F05"
      ]
    },
    {
      "segment_id": "S05",
      "label": "U",
      "global_seconds_exact": [
        "9328319/30000",
        "4671667/15000"
      ],
      "title": "工具布局到人物面部镜头的切点",
      "visual_reason_or_unknown": "主体变化，切点未知。",
      "evidence_frames": [
        "F23",
        "F24"
      ]
    },
    {
      "segment_id": "S06",
      "label": "U",
      "global_seconds_exact": [
        "4671667/15000",
        "330"
      ],
      "title": "连续人物近景的讲述意义",
      "visual_reason_or_unknown": "嘴型持续变化，可能有与过程相关的关键说明；没有音频/转录，不能确认说了什么，也不能默认全部人物近景为NO。视觉上未见手势、工具操作或新结果。",
      "evidence_frames": [
        "F24",
        "F25",
        "F26",
        "F27",
        "F28",
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40",
        "F41",
        "F42",
        "F43",
        "F44",
        "F45",
        "F46",
        "F47",
        "F48",
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "no_interval_note": null,
  "boundary_uncertainty": [
    {
      "segment_id": "S02",
      "label": "U",
      "global_seconds_exact": [
        "9058049/30000",
        "3024021/10000"
      ],
      "title": "操作近景到地面轮胎全景的切点",
      "visual_reason_or_unknown": "手消失并换全景，切点未知；接触后的机械结果未见。",
      "evidence_frames": [
        "F04",
        "F05"
      ]
    },
    {
      "segment_id": "S05",
      "label": "U",
      "global_seconds_exact": [
        "9328319/30000",
        "4671667/15000"
      ],
      "title": "工具布局到人物面部镜头的切点",
      "visual_reason_or_unknown": "主体变化，切点未知。",
      "evidence_frames": [
        "F23",
        "F24"
      ]
    },
    {
      "segment_id": "S06",
      "label": "U",
      "global_seconds_exact": [
        "4671667/15000",
        "330"
      ],
      "title": "连续人物近景的讲述意义",
      "visual_reason_or_unknown": "嘴型持续变化，可能有与过程相关的关键说明；没有音频/转录，不能确认说了什么，也不能默认全部人物近景为NO。视觉上未见手势、工具操作或新结果。",
      "evidence_frames": [
        "F24",
        "F25",
        "F26",
        "F27",
        "F28",
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40",
        "F41",
        "F42",
        "F43",
        "F44",
        "F45",
        "F46",
        "F47",
        "F48",
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "window_edge_uncertainty": {
    "start_bracket_exact": [
      "300",
      "562562/1875"
    ],
    "end_bracket_exact": [
      "989989/3000",
      "330"
    ],
    "interpretation": "窗口边缘极短未采样部分沿相邻可见状态提出初步建议；不声称已逐帧观察"
  },
  "unresolved_event_notes": [
    "轮圈内侧小凸点的具体功能、手是否完成旋紧/释放/测试未能确认；K只指可见接触细节。",
    "喷瓶、扳手、工具盒存在不证明实际使用；静态全景不证明修复成功。",
    "人物近景的解释内容及其在编辑中的必要性需要音频或独立授权的对应内容证据。"
  ],
  "missing_items": [],
  "read_image_inventory": [
    {
      "frame_id": "F00",
      "source_ordinal": 8992,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F00_O008992.png",
      "global_seconds_exact": "562562/1875",
      "local_seconds_exact": "62/1875",
      "png_sha256": "14d030f15bda3a538ef1a85a87325707e45894a8d73c5d6a9f2de462bb824331",
      "rgb_pixel_sha256": "a93ef29d315a50f88e1a1b4949ad7440e886184024513fe29d7c1ff6bb975124",
      "actual_png_sha256": "14d030f15bda3a538ef1a85a87325707e45894a8d73c5d6a9f2de462bb824331",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "轮胎轮圈特写，手拇指与食指在轮圈内侧捏住或接触小凸点"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 9006,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F01_O009006.png",
      "global_seconds_exact": "1502501/5000",
      "local_seconds_exact": "2501/5000",
      "png_sha256": "d92c5c224c7909aa4084b51977c986a0bc919dfbea5c5b3b3163d35fe2a3a3a3",
      "rgb_pixel_sha256": "1c1b32b73d7c620fb1f8aaa993541f31febb735a5705bcb7582cb1ce824b20c0",
      "actual_png_sha256": "d92c5c224c7909aa4084b51977c986a0bc919dfbea5c5b3b3163d35fe2a3a3a3",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "手在轮圈内侧小凸点上持续接触"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 9020,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F02_O009020.png",
      "global_seconds_exact": "451451/1500",
      "local_seconds_exact": "1451/1500",
      "png_sha256": "f0458f4e5096f7e4bd9e1f94572824773f66989d25a43fb5dce48a9ae8e3557f",
      "rgb_pixel_sha256": "330a1f9e4a41fce73a1d78bf7f865813e589e19c4495c1c9844e9b79af9c95ca",
      "actual_png_sha256": "f0458f4e5096f7e4bd9e1f94572824773f66989d25a43fb5dce48a9ae8e3557f",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "手指仍接触轮圈内侧小凸点，轮圈略位移"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 9034,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F03_O009034.png",
      "global_seconds_exact": "4521517/15000",
      "local_seconds_exact": "21517/15000",
      "png_sha256": "9e1b6683fc7b0e25f4405365ac922f94a02fdf00e671c261c0e93b181410b02e",
      "rgb_pixel_sha256": "d313ed9e397b5e3b18bed6ed2e543861c6401c0ed8912eb73d1ef6f6207b9db5",
      "actual_png_sha256": "9e1b6683fc7b0e25f4405365ac922f94a02fdf00e671c261c0e93b181410b02e",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "手指仍接触轮圈内侧小凸点，轮圈与轮胎纹理可见"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 9049,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F04_O009049.png",
      "global_seconds_exact": "9058049/30000",
      "local_seconds_exact": "58049/30000",
      "png_sha256": "744f67db059098b44a19f0961252dcfb5de0dbcb2561a67cabe373d4ef034ca7",
      "rgb_pixel_sha256": "cad75e7524d4861fd52dac63860dc8a738f0ec930981f252ff27d633c1981cc8",
      "actual_png_sha256": "744f67db059098b44a19f0961252dcfb5de0dbcb2561a67cabe373d4ef034ca7",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "手指仍接触轮圈内侧小凸点"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 9063,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F05_O009063.png",
      "global_seconds_exact": "3024021/10000",
      "local_seconds_exact": "24021/10000",
      "png_sha256": "c94f31da9e0e5f46b422788f09b61840dc11ab85eda86b797b084e212d3c2d80",
      "rgb_pixel_sha256": "dbdb00bdf84a067f98511b381465cb935bf5ad7898f05dc830ea7dde86b5bd0a",
      "actual_png_sha256": "c94f31da9e0e5f46b422788f09b61840dc11ab85eda86b797b084e212d3c2d80",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 9077,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F06_O009077.png",
      "global_seconds_exact": "9086077/30000",
      "local_seconds_exact": "86077/30000",
      "png_sha256": "56b8796d008d32fd028f47b706ba1a347be0b3c804ea378eb908199fc8c34b08",
      "rgb_pixel_sha256": "59557f817284fb7364a7f371b17e43859d497b7875884e9a505a0d8da4c833d0",
      "actual_png_sha256": "56b8796d008d32fd028f47b706ba1a347be0b3c804ea378eb908199fc8c34b08",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 9091,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F07_O009091.png",
      "global_seconds_exact": "9100091/30000",
      "local_seconds_exact": "100091/30000",
      "png_sha256": "2f93e7ad30e4d9b0e88c8669017a1c16550ce1ed84c0742e012365ced83ab484",
      "rgb_pixel_sha256": "f31e18513bab402a0f0057049c35bc8ed17d85beb6d29370801a36f5b3919a71",
      "actual_png_sha256": "2f93e7ad30e4d9b0e88c8669017a1c16550ce1ed84c0742e012365ced83ab484",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9106,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F08_O009106.png",
      "global_seconds_exact": "4557553/15000",
      "local_seconds_exact": "57553/15000",
      "png_sha256": "2cd71aa883dd93ceb5ba12c5b4a046e6421b4d6e53703a49eddac5086a99495e",
      "rgb_pixel_sha256": "2c2b0529f830f425a89a1f82c6407aaa80a47f77a436e90cc159d0ea5de1e303",
      "actual_png_sha256": "2cd71aa883dd93ceb5ba12c5b4a046e6421b4d6e53703a49eddac5086a99495e",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 9120,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F09_O009120.png",
      "global_seconds_exact": "38038/125",
      "local_seconds_exact": "538/125",
      "png_sha256": "a1c72fb8ecc3b3a2a82b1dec99e63127f420f9a94c8ef507f1df5d6119acb1b8",
      "rgb_pixel_sha256": "66246997efd162c7c89d60a33e6930ffb1cd4f13ca0cea13c9ee76f4a066891a",
      "actual_png_sha256": "a1c72fb8ecc3b3a2a82b1dec99e63127f420f9a94c8ef507f1df5d6119acb1b8",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 9134,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F10_O009134.png",
      "global_seconds_exact": "4571567/15000",
      "local_seconds_exact": "71567/15000",
      "png_sha256": "2755aa0cb4b9d9a11abcb0d5e45b64845da6e821ad5e84a6d25cc206531e94c3",
      "rgb_pixel_sha256": "1118709d720827a47f73705a8c65f6463fef540988274356a3f2d17ec543f833",
      "actual_png_sha256": "2755aa0cb4b9d9a11abcb0d5e45b64845da6e821ad5e84a6d25cc206531e94c3",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 9148,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F11_O009148.png",
      "global_seconds_exact": "2289287/7500",
      "local_seconds_exact": "39287/7500",
      "png_sha256": "7695dd5354aa651764d3f171698be3685f009ced0bbd1903e7f7abfed7c1471c",
      "rgb_pixel_sha256": "760c66f6e70ef9c780dbecd0be54489776426ef7e5449b864e5184636416d9c0",
      "actual_png_sha256": "7695dd5354aa651764d3f171698be3685f009ced0bbd1903e7f7abfed7c1471c",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 9163,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F12_O009163.png",
      "global_seconds_exact": "9172163/30000",
      "local_seconds_exact": "172163/30000",
      "png_sha256": "02254bb021f03bbda18c34bdc6014eda963d822f5cb14a4b0e0fe467f7ccf299",
      "rgb_pixel_sha256": "b3a7c0f2c38cd1fe85f25324996db61eb38036f03653ccf699dbf003c36452b2",
      "actual_png_sha256": "02254bb021f03bbda18c34bdc6014eda963d822f5cb14a4b0e0fe467f7ccf299",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 9177,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F13_O009177.png",
      "global_seconds_exact": "3062059/10000",
      "local_seconds_exact": "62059/10000",
      "png_sha256": "f8334cb307c95e6ae56cb475a8d0d153b41810ec0b357b748726e2a85ac06b55",
      "rgb_pixel_sha256": "931bcc8e8ebe063e2d78a50051bcc1f69687febd05dd4070ed3bd564f3827455",
      "actual_png_sha256": "f8334cb307c95e6ae56cb475a8d0d153b41810ec0b357b748726e2a85ac06b55",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 9191,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F14_O009191.png",
      "global_seconds_exact": "9200191/30000",
      "local_seconds_exact": "200191/30000",
      "png_sha256": "716686897d7e25935baeb13950a03b8104313dad4de22e846a752b75b0f24f9e",
      "rgb_pixel_sha256": "2605079a7e65b0abc09033104d7bb06e9e4f4dde60e85daf5990b2970bad501b",
      "actual_png_sha256": "716686897d7e25935baeb13950a03b8104313dad4de22e846a752b75b0f24f9e",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 9205,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F15_O009205.png",
      "global_seconds_exact": "1842841/6000",
      "local_seconds_exact": "42841/6000",
      "png_sha256": "794c5b7e97090b8d36b99848419a4d1d054c28887a3eb0160817abb1f9bff7a7",
      "rgb_pixel_sha256": "7194517ffa301a5f4eb02cfc40e5713657bd97161d9d468a9561c55d49f4438c",
      "actual_png_sha256": "794c5b7e97090b8d36b99848419a4d1d054c28887a3eb0160817abb1f9bff7a7",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 9220,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F16_O009220.png",
      "global_seconds_exact": "461461/1500",
      "local_seconds_exact": "11461/1500",
      "png_sha256": "07c91c347b040d7a764c3ddb03b2383822e13dcff4df344dfec6e5e4aa4cbff7",
      "rgb_pixel_sha256": "a04ea2a7ea9734bb6e960c26533b3a07431a32f91214e5424c5717e2a8542a0b",
      "actual_png_sha256": "07c91c347b040d7a764c3ddb03b2383822e13dcff4df344dfec6e5e4aa4cbff7",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 9234,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F17_O009234.png",
      "global_seconds_exact": "1540539/5000",
      "local_seconds_exact": "40539/5000",
      "png_sha256": "9ae78173e5bdef4469d762e58f8c8be827633986e0da2265374427b92edc88b9",
      "rgb_pixel_sha256": "a89596cffa6ba797b808ac93312bbbec20be881a1d9f9a546fe0b8438457d9d2",
      "actual_png_sha256": "9ae78173e5bdef4469d762e58f8c8be827633986e0da2265374427b92edc88b9",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 9248,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F18_O009248.png",
      "global_seconds_exact": "578578/1875",
      "local_seconds_exact": "16078/1875",
      "png_sha256": "9dad24b7462927a8f0b62977b169b32916e913217a4b13d0b271fe305236b698",
      "rgb_pixel_sha256": "b4eb7110aa7f960039989466c0b2438ba075261afe53f69bd93daee022ae885f",
      "actual_png_sha256": "9dad24b7462927a8f0b62977b169b32916e913217a4b13d0b271fe305236b698",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 9262,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F19_O009262.png",
      "global_seconds_exact": "4635631/15000",
      "local_seconds_exact": "135631/15000",
      "png_sha256": "faa726195f6d217e11b7d2a72bc4ae18192d5ddf809979d8ac5a6a80d074fcb1",
      "rgb_pixel_sha256": "ad85b7e90b31a3bd572235a1e45007abf2404ab33555b022cb6827b4ba22c2c0",
      "actual_png_sha256": "faa726195f6d217e11b7d2a72bc4ae18192d5ddf809979d8ac5a6a80d074fcb1",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 9277,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F20_O009277.png",
      "global_seconds_exact": "9286277/30000",
      "local_seconds_exact": "286277/30000",
      "png_sha256": "7ef56abddd563b64315e3beb24a608b81f4df0ad1bb9303bd9bfcc581c8e17db",
      "rgb_pixel_sha256": "d83922ee6c34025a7258bdc963b73417049dc673b35138326d9e7e5e33d85b99",
      "actual_png_sha256": "7ef56abddd563b64315e3beb24a608b81f4df0ad1bb9303bd9bfcc581c8e17db",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 9291,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F21_O009291.png",
      "global_seconds_exact": "3100097/10000",
      "local_seconds_exact": "100097/10000",
      "png_sha256": "8df7b90f77b85ef9404b2b98daa52e24d5705dc86c48750682f03390ba83ce30",
      "rgb_pixel_sha256": "abc8490ce32d4747682ed0c7663e87cef1c62d53f9521aafb6e371f8f20393b5",
      "actual_png_sha256": "8df7b90f77b85ef9404b2b98daa52e24d5705dc86c48750682f03390ba83ce30",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 9305,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F22_O009305.png",
      "global_seconds_exact": "1862861/6000",
      "local_seconds_exact": "62861/6000",
      "png_sha256": "f64a221a36e61b09de1fa1cc0688034d5ea4c7ff5510b86202f74732dee26218",
      "rgb_pixel_sha256": "5bbf2de0dfb8d285427f4b264a75e8676495d8f4b0e9d8d9d584a1bcbd7ba327",
      "actual_png_sha256": "f64a221a36e61b09de1fa1cc0688034d5ea4c7ff5510b86202f74732dee26218",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 9319,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F23_O009319.png",
      "global_seconds_exact": "9328319/30000",
      "local_seconds_exact": "328319/30000",
      "png_sha256": "25eb85e0812a3952d17bc076a89e6460db4cc7247b48a48c593160c8703a1bae",
      "rgb_pixel_sha256": "0d079f456af63f0d134d8b8030f3341ed53222665be3451aecec32c06d763ce9",
      "actual_png_sha256": "25eb85e0812a3952d17bc076a89e6460db4cc7247b48a48c593160c8703a1bae",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "轮胎平放在水泥地，轮圈朝上；右侧有白色喷瓶、可调扳手，右边缘红色工具盒局部；物品静止"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 9334,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F24_O009334.png",
      "global_seconds_exact": "4671667/15000",
      "local_seconds_exact": "171667/15000",
      "png_sha256": "a4bd02105bd40595cfd35616e1692cc8034a12ee286c167c905be41fd232b0c3",
      "rgb_pixel_sha256": "1682417856b16f6e099370d0f644e9fd19045267534a282a7c5f1b7f58f41723",
      "actual_png_sha256": "a4bd02105bd40595cfd35616e1692cc8034a12ee286c167c905be41fd232b0c3",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 9348,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F25_O009348.png",
      "global_seconds_exact": "779779/2500",
      "local_seconds_exact": "29779/2500",
      "png_sha256": "9d76d1d0cc474723e725eeb37b289834bc05f3ee1f089859f607a3ed6a708de1",
      "rgb_pixel_sha256": "5c8f3e8908042aac53061115be5caaabac08260a777cdaffa78ec05c49142ede",
      "actual_png_sha256": "9d76d1d0cc474723e725eeb37b289834bc05f3ee1f089859f607a3ed6a708de1",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 9362,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F26_O009362.png",
      "global_seconds_exact": "4685681/15000",
      "local_seconds_exact": "185681/15000",
      "png_sha256": "509cd1a1ff11b3f20cdb7970c2bbd12e2beb6cb7b9a42af220352a9672b1dd92",
      "rgb_pixel_sha256": "a9acb033811220a6a2e0726ab0e3fc05defb1b55868fe6920f590584d7c42530",
      "actual_png_sha256": "509cd1a1ff11b3f20cdb7970c2bbd12e2beb6cb7b9a42af220352a9672b1dd92",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 9376,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F27_O009376.png",
      "global_seconds_exact": "586586/1875",
      "local_seconds_exact": "24086/1875",
      "png_sha256": "fef193f5043932c309cae7e5511274593c03dff5f644b0ae45de847ba45079e8",
      "rgb_pixel_sha256": "e565faf7d3a2ffa760f277da7a7815f71d0ea69d5c41738b568703420512dd06",
      "actual_png_sha256": "fef193f5043932c309cae7e5511274593c03dff5f644b0ae45de847ba45079e8",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 9391,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F28_O009391.png",
      "global_seconds_exact": "9400391/30000",
      "local_seconds_exact": "400391/30000",
      "png_sha256": "eabcdbaee3d598062412dd3718322795cab223b2cb64cdb5aa7cf550b2a5e981",
      "rgb_pixel_sha256": "cc95437dc9886de221f35398b40011ecb71a7d9398dbf2697cdd702a96dcd973",
      "actual_png_sha256": "eabcdbaee3d598062412dd3718322795cab223b2cb64cdb5aa7cf550b2a5e981",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 9405,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F29_O009405.png",
      "global_seconds_exact": "627627/2000",
      "local_seconds_exact": "27627/2000",
      "png_sha256": "e7bb9bbd765f1bc87e9dd9b2b99cb50114488f4943ff87604e6f5ce8cf5fb802",
      "rgb_pixel_sha256": "13d89860b7e6e7b9eb14b8ea83c537d5f283e4e6e0aa212958a1215d73a4bad5",
      "actual_png_sha256": "e7bb9bbd765f1bc87e9dd9b2b99cb50114488f4943ff87604e6f5ce8cf5fb802",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 9419,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F30_O009419.png",
      "global_seconds_exact": "9428419/30000",
      "local_seconds_exact": "428419/30000",
      "png_sha256": "8b825b3342ff53092dbf8cbb824afc107835a8358aca4ff31be3370e01b057b1",
      "rgb_pixel_sha256": "fed7fb47c0bc7a15b9bf1f9f79e56b5290ea098421bb1068f22ea0268f6a0535",
      "actual_png_sha256": "8b825b3342ff53092dbf8cbb824afc107835a8358aca4ff31be3370e01b057b1",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 9433,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F31_O009433.png",
      "global_seconds_exact": "9442433/30000",
      "local_seconds_exact": "442433/30000",
      "png_sha256": "8b8663eb0e97483ba7764267635b4a47ff041445e1fcc5c24b146697b2eb3044",
      "rgb_pixel_sha256": "6dd1514fb2d3b1ca93f3e4fa333c02b567272829dccef665f48542e8e549cc2b",
      "actual_png_sha256": "8b8663eb0e97483ba7764267635b4a47ff041445e1fcc5c24b146697b2eb3044",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 9448,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F32_O009448.png",
      "global_seconds_exact": "1182181/3750",
      "local_seconds_exact": "57181/3750",
      "png_sha256": "10e72a1f4e85b5e894aa01f64ac2ebf30f2b154820210cb64df7bca39e97af1f",
      "rgb_pixel_sha256": "931ce9be37e3d23d5adabd907e2bce0575e988ec04033d289dadc20dc8c1e26b",
      "actual_png_sha256": "10e72a1f4e85b5e894aa01f64ac2ebf30f2b154820210cb64df7bca39e97af1f",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 9462,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F33_O009462.png",
      "global_seconds_exact": "1578577/5000",
      "local_seconds_exact": "78577/5000",
      "png_sha256": "3e98f9e65aa9f8d9288159208f43919689ff8d7fa3a24bc5f4a58dfc909737fe",
      "rgb_pixel_sha256": "d140b6855a96a05a26fd83745d4a9ace0a4ca6ee1d9cb8ed775f6f767ca251a9",
      "actual_png_sha256": "3e98f9e65aa9f8d9288159208f43919689ff8d7fa3a24bc5f4a58dfc909737fe",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 9476,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F34_O009476.png",
      "global_seconds_exact": "2371369/7500",
      "local_seconds_exact": "121369/7500",
      "png_sha256": "a8f6b86eded4ee6a4a237a918be700577dac822a3aa75304eeb68292210a8d05",
      "rgb_pixel_sha256": "6c27bb5803a47802b7ebe256d1a06295b04e7225ec4ddfff5cb0f1d1f3a65a39",
      "actual_png_sha256": "a8f6b86eded4ee6a4a237a918be700577dac822a3aa75304eeb68292210a8d05",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 9490,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F35_O009490.png",
      "global_seconds_exact": "949949/3000",
      "local_seconds_exact": "49949/3000",
      "png_sha256": "1c365c441a32a5628388309d953187640e26c4f4d86e8b2960adedc7d4109c4d",
      "rgb_pixel_sha256": "f18ed9836c03772122ae3f05613cd917c1eefa6fb184d41e5447eb6e25cdf8f1",
      "actual_png_sha256": "1c365c441a32a5628388309d953187640e26c4f4d86e8b2960adedc7d4109c4d",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 9505,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F36_O009505.png",
      "global_seconds_exact": "1902901/6000",
      "local_seconds_exact": "102901/6000",
      "png_sha256": "9b00fb55dd62e88fa0c480f1087d398155768fa5bb4613a39c8da61b43f87841",
      "rgb_pixel_sha256": "19ffd5abb2874775d2e6c44276d42fc7f1a1eb734337d14fd6db13fdaa37d4e4",
      "actual_png_sha256": "9b00fb55dd62e88fa0c480f1087d398155768fa5bb4613a39c8da61b43f87841",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 9519,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F37_O009519.png",
      "global_seconds_exact": "3176173/10000",
      "local_seconds_exact": "176173/10000",
      "png_sha256": "a3a70d33729fffc2eaea0c04584d78f46fd6d96b7ff9f5b0625903692602c5ac",
      "rgb_pixel_sha256": "ad16d9db3e8d3e88823c957a5a0cbf6f8e4234148ea2e4be7e93470fdcfc4efb",
      "actual_png_sha256": "a3a70d33729fffc2eaea0c04584d78f46fd6d96b7ff9f5b0625903692602c5ac",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 9533,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F38_O009533.png",
      "global_seconds_exact": "9542533/30000",
      "local_seconds_exact": "542533/30000",
      "png_sha256": "829d69b643cabdf1be137893dfa0a4ca164115aa06075bd5c531a79cc786aca8",
      "rgb_pixel_sha256": "468a035d24421d4fb37389b72e627bee48a187bc187b5a8de94fceea905a21ea",
      "actual_png_sha256": "829d69b643cabdf1be137893dfa0a4ca164115aa06075bd5c531a79cc786aca8",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 9547,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F39_O009547.png",
      "global_seconds_exact": "9556547/30000",
      "local_seconds_exact": "556547/30000",
      "png_sha256": "54e81ca8167c100ff83074f867fa5d572e103f628285626b51e02b7aa49f8f63",
      "rgb_pixel_sha256": "f9f4076f0896bc72a0e4dc233dc4a032746c9dfc13185a85d8d6f76a9dfe6bda",
      "actual_png_sha256": "54e81ca8167c100ff83074f867fa5d572e103f628285626b51e02b7aa49f8f63",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 9562,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F40_O009562.png",
      "global_seconds_exact": "4785781/15000",
      "local_seconds_exact": "285781/15000",
      "png_sha256": "3907e057d4f186b4d3f2888212c961cc12aef7984835fbf6f42a03b4c0ab77cc",
      "rgb_pixel_sha256": "066ae16656a65a8d7d8c64b977d54fc3573a6389eae6928ae446a932360b2822",
      "actual_png_sha256": "3907e057d4f186b4d3f2888212c961cc12aef7984835fbf6f42a03b4c0ab77cc",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 9576,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F41_O009576.png",
      "global_seconds_exact": "399399/1250",
      "local_seconds_exact": "24399/1250",
      "png_sha256": "e98242ce12409ff41996cf8ebff59b9c12f4c3514326ec9e45490a67bfeaadb1",
      "rgb_pixel_sha256": "2c130c321f7a5615a54c51a53167a7cb04767a504e0b507a1aab885e21c04c82",
      "actual_png_sha256": "e98242ce12409ff41996cf8ebff59b9c12f4c3514326ec9e45490a67bfeaadb1",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 9590,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F42_O009590.png",
      "global_seconds_exact": "959959/3000",
      "local_seconds_exact": "59959/3000",
      "png_sha256": "9f8606ad353f8c28ca0f3e31ddf71dee687f4d44fffd0430fb53b5c14ba51afb",
      "rgb_pixel_sha256": "b872719065487360b64b7421219ed9e9bcd581ca0b403e8adb0bb79900fb2613",
      "actual_png_sha256": "9f8606ad353f8c28ca0f3e31ddf71dee687f4d44fffd0430fb53b5c14ba51afb",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 9604,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F43_O009604.png",
      "global_seconds_exact": "2403401/7500",
      "local_seconds_exact": "153401/7500",
      "png_sha256": "7db85403fe5b3553b1499b7dffc85a63ca67951f2fd646eedb44e2550773aaf2",
      "rgb_pixel_sha256": "35ed8d59df8899e1b3ed3eae6437bf54b8bf49f0ff43c210a182c8b6bc7ac4ad",
      "actual_png_sha256": "7db85403fe5b3553b1499b7dffc85a63ca67951f2fd646eedb44e2550773aaf2",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 9619,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F44_O009619.png",
      "global_seconds_exact": "9628619/30000",
      "local_seconds_exact": "628619/30000",
      "png_sha256": "159f2619870bd585a997f05a59027ddbcbd5a461974ab21e1b0d06f4f77be5f5",
      "rgb_pixel_sha256": "064229e6a126f486b3411a495e18e3581148e4d1c309b2cdcaac100a6d15a87a",
      "actual_png_sha256": "159f2619870bd585a997f05a59027ddbcbd5a461974ab21e1b0d06f4f77be5f5",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 9633,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F45_O009633.png",
      "global_seconds_exact": "3214211/10000",
      "local_seconds_exact": "214211/10000",
      "png_sha256": "ab8b1111f66c8c1c7dd04e44604e8bcabf106c44b966fc1e82b1813d637e454e",
      "rgb_pixel_sha256": "1efbb85f0695c71f9b77eec50d7ddec23d54ff0e1120783e4c6278b3d581fbbd",
      "actual_png_sha256": "ab8b1111f66c8c1c7dd04e44604e8bcabf106c44b966fc1e82b1813d637e454e",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 9647,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F46_O009647.png",
      "global_seconds_exact": "9656647/30000",
      "local_seconds_exact": "656647/30000",
      "png_sha256": "5287fcc577bc4a63c620af23fec4d692eb7b05eae62e0eac05aa7827e1ddfa99",
      "rgb_pixel_sha256": "fa8bade6fbbbc366349f113369ec499f60c6332b524e5650f1d936931b4a49a0",
      "actual_png_sha256": "5287fcc577bc4a63c620af23fec4d692eb7b05eae62e0eac05aa7827e1ddfa99",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 9661,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F47_O009661.png",
      "global_seconds_exact": "9670661/30000",
      "local_seconds_exact": "670661/30000",
      "png_sha256": "5e60d11f71014f1db101840ea7b7f841c9ad4690ab54190afa3feaec8b9607ff",
      "rgb_pixel_sha256": "b1bc897e8ec19c88201c9ceb1729c20a866e81d1cca0df8d6c3aeaec359914eb",
      "actual_png_sha256": "5e60d11f71014f1db101840ea7b7f841c9ad4690ab54190afa3feaec8b9607ff",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 9676,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F48_O009676.png",
      "global_seconds_exact": "2421419/7500",
      "local_seconds_exact": "171419/7500",
      "png_sha256": "9091d91fcdd48b21b1ac7e61f5bfda2d8242c510386ae6f40ad07663b883155c",
      "rgb_pixel_sha256": "634711de6454a69cd0a1f4cbca509167c859a160a85e4ef459dc70df2f7fde3e",
      "actual_png_sha256": "9091d91fcdd48b21b1ac7e61f5bfda2d8242c510386ae6f40ad07663b883155c",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 9690,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F49_O009690.png",
      "global_seconds_exact": "323323/1000",
      "local_seconds_exact": "23323/1000",
      "png_sha256": "b03487eb221bbd0747d078686904ee87ae22df1c5f482c0c90c56c8d1213e33f",
      "rgb_pixel_sha256": "6edfd0da3cb034101685db4a788201146229b8b738d842a79e9a940d84c0e2b2",
      "actual_png_sha256": "b03487eb221bbd0747d078686904ee87ae22df1c5f482c0c90c56c8d1213e33f",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 9704,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F50_O009704.png",
      "global_seconds_exact": "1214213/3750",
      "local_seconds_exact": "89213/3750",
      "png_sha256": "c0366e31dc9bb510383f926d4de620b81ca841d7aee77d7b84a8868942e84214",
      "rgb_pixel_sha256": "64190a5cd0a50d02c1cc0ebd05795e841c3e9bcfa9bedac318905be4996c07d9",
      "actual_png_sha256": "c0366e31dc9bb510383f926d4de620b81ca841d7aee77d7b84a8868942e84214",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 9718,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F51_O009718.png",
      "global_seconds_exact": "4863859/15000",
      "local_seconds_exact": "363859/15000",
      "png_sha256": "3fd9515329e610b4eb66083ddfb7dc2993281b9ba2b655fc6369536f4b6078cc",
      "rgb_pixel_sha256": "20d8863aed713a41992838822eb7a7016dde5e3933b39a5214df54b21eb46d30",
      "actual_png_sha256": "3fd9515329e610b4eb66083ddfb7dc2993281b9ba2b655fc6369536f4b6078cc",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 9733,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F52_O009733.png",
      "global_seconds_exact": "9742733/30000",
      "local_seconds_exact": "742733/30000",
      "png_sha256": "f62e79cad7373e0dcff95cc8e7534dd955d6ae40f414a8eee3c10fe25b434fab",
      "rgb_pixel_sha256": "be3d6576a7d28614f9e911ab8c29acb0d46135147c9b177f894931926f4f805a",
      "actual_png_sha256": "f62e79cad7373e0dcff95cc8e7534dd955d6ae40f414a8eee3c10fe25b434fab",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 9747,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F53_O009747.png",
      "global_seconds_exact": "3252249/10000",
      "local_seconds_exact": "252249/10000",
      "png_sha256": "594acaf7669da00a1347b3b6f3fc6e9d98a68c982387417759bea3e4c77490f1",
      "rgb_pixel_sha256": "90cab60e7ad7cf7f359b4cf5edc562857aa99c1b88da43b049657c8741edf4ba",
      "actual_png_sha256": "594acaf7669da00a1347b3b6f3fc6e9d98a68c982387417759bea3e4c77490f1",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 9761,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F54_O009761.png",
      "global_seconds_exact": "9770761/30000",
      "local_seconds_exact": "770761/30000",
      "png_sha256": "6415aac1f6e6534daea5fce287099ec9628173a2f99b42fa28e52dc43eb20eeb",
      "rgb_pixel_sha256": "5ce9611037db4973f622c6f67aa53a8d7f87b4aa38c22c7ba22b35427902243e",
      "actual_png_sha256": "6415aac1f6e6534daea5fce287099ec9628173a2f99b42fa28e52dc43eb20eeb",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 9775,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F55_O009775.png",
      "global_seconds_exact": "391391/1200",
      "local_seconds_exact": "31391/1200",
      "png_sha256": "2d146b7d4e429f785813951a7bae52af5ba4c9e68c525ad2a538313d9dc0e0f5",
      "rgb_pixel_sha256": "8d9d08350cf02f212a948d9ca44ff84d94767e2886e2aceef3f9d18a9c2c6065",
      "actual_png_sha256": "2d146b7d4e429f785813951a7bae52af5ba4c9e68c525ad2a538313d9dc0e0f5",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 9790,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F56_O009790.png",
      "global_seconds_exact": "979979/3000",
      "local_seconds_exact": "79979/3000",
      "png_sha256": "44dee735c158d3feda20dd1765ef5f3c3dcf0155108b84fbd02ab1a551704fcf",
      "rgb_pixel_sha256": "292714c211ddf8a9473cad235567e4c2008d32e4f6dc1cda4492fb92887acb2b",
      "actual_png_sha256": "44dee735c158d3feda20dd1765ef5f3c3dcf0155108b84fbd02ab1a551704fcf",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 9804,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F57_O009804.png",
      "global_seconds_exact": "817817/2500",
      "local_seconds_exact": "67817/2500",
      "png_sha256": "98dfc1ca7158880c8f0b60a29ef1edaafca0bd9f6ab8b704ffa56a0d4efcd726",
      "rgb_pixel_sha256": "f4c8d950aba8e2a8b85371d9dd512e09aa772ec70de44aff47e31785e4de50bd",
      "actual_png_sha256": "98dfc1ca7158880c8f0b60a29ef1edaafca0bd9f6ab8b704ffa56a0d4efcd726",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 9818,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F58_O009818.png",
      "global_seconds_exact": "4913909/15000",
      "local_seconds_exact": "413909/15000",
      "png_sha256": "616dfe7d37b6184e33a77416e86c47a131ec73cd5b2ee4bcf721302c65ea68de",
      "rgb_pixel_sha256": "acb9729f06601fa0bc3875b809dc2be940885ab218a9a6239582c0d2a7caa5a0",
      "actual_png_sha256": "616dfe7d37b6184e33a77416e86c47a131ec73cd5b2ee4bcf721302c65ea68de",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 9832,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F59_O009832.png",
      "global_seconds_exact": "1230229/3750",
      "local_seconds_exact": "105229/3750",
      "png_sha256": "d390127081eae0c359d48735f753ce03468f6fd238e6b7fcf99bf13461bb767e",
      "rgb_pixel_sha256": "ae696faad5bfc6dea23ff6d42c96005b11ad0bd0539cf13a6a757bf49ceafc20",
      "actual_png_sha256": "d390127081eae0c359d48735f753ce03468f6fd238e6b7fcf99bf13461bb767e",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 9847,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F60_O009847.png",
      "global_seconds_exact": "9856847/30000",
      "local_seconds_exact": "856847/30000",
      "png_sha256": "b5a158f904a4791cc10b091c29b1104a1e0f379b3220992d09d2537b0e1cf7d0",
      "rgb_pixel_sha256": "fc04fa970f90bdbb61693513cd23f5918b8fdeabcc7bcc98d24cabb62a2d3eb6",
      "actual_png_sha256": "b5a158f904a4791cc10b091c29b1104a1e0f379b3220992d09d2537b0e1cf7d0",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 9861,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F61_O009861.png",
      "global_seconds_exact": "3290287/10000",
      "local_seconds_exact": "290287/10000",
      "png_sha256": "3ac17488ce319f83b386882a70569f0ef5ee28795700fa9da4d947a7aea98d3a",
      "rgb_pixel_sha256": "9cb3a8d393dc88be6dc7cdf156278066ec55b7bb17d5a7b4f12eefdd6b626c6f",
      "actual_png_sha256": "3ac17488ce319f83b386882a70569f0ef5ee28795700fa9da4d947a7aea98d3a",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 9875,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F62_O009875.png",
      "global_seconds_exact": "79079/240",
      "local_seconds_exact": "7079/240",
      "png_sha256": "5bb0360f640b963db196a0ab0b2543537e274b8a04b499312a662f215a92d480",
      "rgb_pixel_sha256": "d5b83085e35050ef369a94bdd5e226377aded86ff5cd2adb283f887ad1841bba",
      "actual_png_sha256": "5bb0360f640b963db196a0ab0b2543537e274b8a04b499312a662f215a92d480",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 9890,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\frames\\F63_O009890.png",
      "global_seconds_exact": "989989/3000",
      "local_seconds_exact": "89989/3000",
      "png_sha256": "032639964cf79c05fc901072ba138a51d6056bfe8fb018f328fe39be9823484b",
      "rgb_pixel_sha256": "a96a947684b7e5de5328bdecaef5d6d996b5291675fb47a0b3f407d1ef8cd1d7",
      "actual_png_sha256": "032639964cf79c05fc901072ba138a51d6056bfe8fb018f328fe39be9823484b",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；未见手或工具操作"
    }
  ]
}



## 完整新增公开证据：02_AwmHb44_ouw_W10.independent_initial_blind_v1.md
