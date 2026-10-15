        "553553/7500"
      ],
      "title": "犬贴近镜头的严重失焦段",
      "visual_reason_or_unknown": "失焦与草遮挡使头身动作细节不可判；可能影响是否应保留新的姿态变化。",
      "evidence_frames": [
        "F25",
        "F26",
        "F27",
        "F28",
        "F29"
      ]
    },
    {
      "segment_id": "S11",
      "label": "U",
      "global_seconds_exact": [
        "553553/7500",
        "761761/10000"
      ],
      "title": "前身压低与爪位变化的短镜头",
      "visual_reason_or_unknown": "可以看见身体前移和前爪位移，但低清样本不足区分普通移步、蹲坐变化或其他动作；不编造清理、排便、抓挠。",
      "evidence_frames": [
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34"
      ]
    },
    {
      "segment_id": "S12",
      "label": "U",
      "global_seconds_exact": [
        "761761/10000",
        "2371369/30000"
      ],
      "title": "侧脸近景的初始失焦段",
      "visual_reason_or_unknown": "犬脸明显失焦，清晰肖像应从何时开始无法在样本间精确确认。",
      "evidence_frames": [
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40"
      ]
    },
    {
      "segment_id": "S13",
      "label": "K",
      "global_seconds_exact": [
        "2371369/30000",
        "2413411/30000"
      ],
      "title": "阳光下的侧脸与透光竖耳",
      "visual_reason_or_unknown": "脸部纹理、鼻与红色透光耳清楚，静态构图有信息。",
      "evidence_frames": [
        "F40",
        "F41",
        "F42",
        "F43"
      ]
    },
    {
      "segment_id": "S14",
      "label": "NO",
      "global_seconds_exact": [
        "2413411/30000",
        "409409/5000"
      ],
      "title": "清晰侧脸重复持留",
      "visual_reason_or_unknown": "已建立侧脸，后续姿态接近重复；无需全部持留。",
      "evidence_frames": [
        "F43",
        "F44",
        "F45",
        "F46"
      ]
    },
    {
      "segment_id": "S15",
      "label": "K",
      "global_seconds_exact": [
        "409409/5000",
        "2499497/30000"
      ],
      "title": "犬转头后眼睑下垂的近景",
      "visual_reason_or_unknown": "头向左前转的变化与眼睑状态清楚，保留起态及结果；不据此断言睡眠或情绪。",
      "evidence_frames": [
        "F46",
        "F47",
        "F48",
        "F49"
      ]
    },
    {
      "segment_id": "S16",
      "label": "NO",
      "global_seconds_exact": [
        "2499497/30000",
        "107107/1250"
      ],
      "title": "近景眼睑状态重复持留",
      "visual_reason_or_unknown": "相同头部构图和眼睑状态已呈现，后续新视觉信息少。",
      "evidence_frames": [
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54"
      ]
    },
    {
      "segment_id": "S17",
      "label": "U",
      "global_seconds_exact": [
        "107107/1250",
        "667667/7500"
      ],
      "title": "草地前景与卧犬之间的焦点过渡",
      "visual_reason_or_unknown": "发生镜头/焦点变化，起初犬严重失焦；其间准确姿态与可用清晰起点待确认。",
      "evidence_frames": [
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61"
      ]
    },
    {
      "segment_id": "S18",
      "label": "K",
      "global_seconds_exact": [
        "667667/7500",
        "90"
      ],
      "title": "草地卧犬抬头的清晰结果",
      "visual_reason_or_unknown": "身体侧卧、头抬起、竖耳与右前方视线清楚，适合作结尾静态结果；不推断思考或放松动机。",
      "evidence_frames": [
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "unresolved_for_full_window": {
    "frames": [
      "F02",
      "F03",
      "F17",
      "F18",
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
      "F54",
      "F55",
      "F56",
      "F57",
      "F58",
      "F59",
      "F60",
      "F61"
    ],
    "issue": "切点、严重失焦与短爪位变化区间保留具体U，可能影响独立事件选择或清晰段边界；稳定可见重复间隙未扩大U。",
    "affects_full_window_target": true
  },
  "limitations": [
    "有效视图是inverse patch及inverse normalization后round uint8的显示重构；不能把PNG字节等同于归一化model tensor。tensor SHA与机器回执独立绑定。",
    "所有64采样视图已看，但完整native帧未看，具体切点和识别不清事件保留U。",
    "processor文件SHA与Linux实际元数据回执绑定，不证明Linux已经运行相同processor。",
    "可见性通过不等于训练准入、金标或冻结完整窗口目标。"
  ],
  "student_view_inventory": [
    {
      "frame_id": "F00",
      "source_ordinal": 1799,
      "global_seconds_exact": "1800799/30000",
      "local_seconds_exact": "799/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F00_student.png",
      "png_sha256": "900a4511ea96b60d6b30435f81ac26e10f425fe676067923239f2b00062b5143",
      "rgb_pixel_sha256": "075b1d8642e1d33fa4391298bdfa829b040ff06e1683cfa97e3f4bfb69ecba23",
      "actual_png_sha256": "900a4511ea96b60d6b30435f81ac26e10f425fe676067923239f2b00062b5143",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 1813,
      "global_seconds_exact": "1814813/30000",
      "local_seconds_exact": "14813/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F01_student.png",
      "png_sha256": "b5834bcd9c0ac92ec89849a65c36fba7e4301c4c2371b79c777b064cc424ea04",
      "rgb_pixel_sha256": "b16853e604c869756ed9d711ae70c90811b981566f609add71449c9c57a00221",
      "actual_png_sha256": "b5834bcd9c0ac92ec89849a65c36fba7e4301c4c2371b79c777b064cc424ea04",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 1827,
      "global_seconds_exact": "609609/10000",
      "local_seconds_exact": "9609/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F02_student.png",
      "png_sha256": "f9a8423b8c4d6cb358bf4b6ed92af99663b3d241e771edacf09b06bb1a104513",
      "rgb_pixel_sha256": "33ac45683e080a078eb3f07411454ddff906822ec97e8bb725e6a88db18d735f",
      "actual_png_sha256": "f9a8423b8c4d6cb358bf4b6ed92af99663b3d241e771edacf09b06bb1a104513",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 1841,
      "global_seconds_exact": "1842841/30000",
      "local_seconds_exact": "42841/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F03_student.png",
      "png_sha256": "03b997719290db95d44b4c62049ebf6a0b56dacdabc0e358852ec47ffb6d390a",
      "rgb_pixel_sha256": "6226291b0a726cf95242de9aa0014a2022577ff063fc6b276cf8a7f3a554171e",
      "actual_png_sha256": "03b997719290db95d44b4c62049ebf6a0b56dacdabc0e358852ec47ffb6d390a",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 1856,
      "global_seconds_exact": "116116/1875",
      "local_seconds_exact": "3616/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F04_student.png",
      "png_sha256": "1356e606c9bad4711475992bad84044dfa1465dc2f69a2cebbc46b8c487b24af",
      "rgb_pixel_sha256": "116ba9fa2d8c70c65cde9c43a63a7590bea5f24751c5a284f094c77da906a193",
      "actual_png_sha256": "1356e606c9bad4711475992bad84044dfa1465dc2f69a2cebbc46b8c487b24af",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 1870,
      "global_seconds_exact": "187187/3000",
      "local_seconds_exact": "7187/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F05_student.png",
      "png_sha256": "c96eb61e61a83f4e7acf91806732d5150cda6c6aca62b6c58d237860f665ed5b",
      "rgb_pixel_sha256": "af5aee278110ee9c79cffe5d4067552c6e25134922185ba9766e8501f4061bc6",
      "actual_png_sha256": "c96eb61e61a83f4e7acf91806732d5150cda6c6aca62b6c58d237860f665ed5b",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 1884,
      "global_seconds_exact": "157157/2500",
      "local_seconds_exact": "7157/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F06_student.png",
      "png_sha256": "75dd20068eb9781cec054b38dcb6e15d43ae883196a90eabad2e809b3c94018b",
      "rgb_pixel_sha256": "1e8455074943be77bb6622dc30a123feec28effdc1cbb305cc388b711f020bd7",
      "actual_png_sha256": "75dd20068eb9781cec054b38dcb6e15d43ae883196a90eabad2e809b3c94018b",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 1898,
      "global_seconds_exact": "949949/15000",
      "local_seconds_exact": "49949/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F07_student.png",
      "png_sha256": "cf3aafafa5acc69e9a836159865c65b3985c520994ac155e4e1bb22abf8ca60b",
      "rgb_pixel_sha256": "30b931b835643b3071ed291b4e55dc04674658979948ffacf3336bf3ddb311ae",
      "actual_png_sha256": "cf3aafafa5acc69e9a836159865c65b3985c520994ac155e4e1bb22abf8ca60b",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 1913,
      "global_seconds_exact": "1914913/30000",
      "local_seconds_exact": "114913/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F08_student.png",
      "png_sha256": "a4957292097e90be485a3fc06f75fab614cb0b4d013dcfaa777f703ee91fa1c4",
      "rgb_pixel_sha256": "ea6228b74bfe7b901e4435b07a2932bcae150d35ace47a98911e89a694c9d50b",
      "actual_png_sha256": "a4957292097e90be485a3fc06f75fab614cb0b4d013dcfaa777f703ee91fa1c4",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 1927,
      "global_seconds_exact": "1928927/30000",
      "local_seconds_exact": "128927/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F09_student.png",
      "png_sha256": "f628ce33b6540354ad75e100b4d513de8d2dea27cc081ea2bea87a70ad321afe",
      "rgb_pixel_sha256": "8269675599bd81573a5faaafc210245c27907e9ef577ec8aed9a28800db1bf29",
      "actual_png_sha256": "f628ce33b6540354ad75e100b4d513de8d2dea27cc081ea2bea87a70ad321afe",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 1941,
      "global_seconds_exact": "647647/10000",
      "local_seconds_exact": "47647/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F10_student.png",
      "png_sha256": "a3e02f84cac6b75574eac2ca293fb4b10ac8a49fce14aca5f20c0e7c4b3e6da3",
      "rgb_pixel_sha256": "761f81bf5030646eda4129a93f2112cd82e2d0f06476754db1098c4ec5596a6b",
      "actual_png_sha256": "a3e02f84cac6b75574eac2ca293fb4b10ac8a49fce14aca5f20c0e7c4b3e6da3",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 1955,
      "global_seconds_exact": "391391/6000",
      "local_seconds_exact": "31391/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F11_student.png",
      "png_sha256": "4830a3f6ca57400f7a3c71866d6691f8a63213e8ffdc6bf1fb7ef70846368dcd",
      "rgb_pixel_sha256": "4cd8b662734208e901593d9fd1b9a46c981e6807154c4951fc14409f2cef44f9",
      "actual_png_sha256": "4830a3f6ca57400f7a3c71866d6691f8a63213e8ffdc6bf1fb7ef70846368dcd",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 1970,
      "global_seconds_exact": "197197/3000",
      "local_seconds_exact": "17197/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F12_student.png",
      "png_sha256": "ec08def44a091b2dd7b25c8529f2bb583a8d3282e00f470be7ba1f7c70ab817e",
      "rgb_pixel_sha256": "17ee7d1003102f88a7c06126fca50f6071d5812c9f42f4577466dac3e06ad2f9",
      "actual_png_sha256": "ec08def44a091b2dd7b25c8529f2bb583a8d3282e00f470be7ba1f7c70ab817e",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 1984,
      "global_seconds_exact": "124124/1875",
      "local_seconds_exact": "11624/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F13_student.png",
      "png_sha256": "df0810e1e50599dff34ffc0631bf8a4e910a317269e78ecb2f307a362c187591",
      "rgb_pixel_sha256": "3578ed7c32799d1e9df10724ff133e8c796b584de655a259cf726c6c0699057c",
      "actual_png_sha256": "df0810e1e50599dff34ffc0631bf8a4e910a317269e78ecb2f307a362c187591",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 1998,
      "global_seconds_exact": "333333/5000",
      "local_seconds_exact": "33333/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F14_student.png",
      "png_sha256": "c93a2c4464005aa64b77d242e07ad820c9f01906a83a606a9865220c09f08139",
      "rgb_pixel_sha256": "4a28f7f76cd33bd7ee78f89db4674a7518408f2283cc6c0cfb8e0f59f2a8b7f2",
      "actual_png_sha256": "c93a2c4464005aa64b77d242e07ad820c9f01906a83a606a9865220c09f08139",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 2012,
      "global_seconds_exact": "503503/7500",
      "local_seconds_exact": "53503/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F15_student.png",
      "png_sha256": "28b0cc952ba04233ce7edd77eef2e012fdf361cba00d034cc258f8677d9115e7",
      "rgb_pixel_sha256": "48342ebabc5577939fd284bf109d3dcfeca0bdcca26a11627c033ec7d68fdb2f",
      "actual_png_sha256": "28b0cc952ba04233ce7edd77eef2e012fdf361cba00d034cc258f8677d9115e7",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 2027,
      "global_seconds_exact": "2029027/30000",
      "local_seconds_exact": "229027/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F16_student.png",
      "png_sha256": "0a2d7ce9ce9b79de4cc0248d2198a0779b6237797a49d6cbbc11ee278ab8b5cc",
      "rgb_pixel_sha256": "c39862c24561da5a113d4864b82faa8bc42da7a4abe4f10e50d18f0b86b9d060",
      "actual_png_sha256": "0a2d7ce9ce9b79de4cc0248d2198a0779b6237797a49d6cbbc11ee278ab8b5cc",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 2041,
      "global_seconds_exact": "2043041/30000",
      "local_seconds_exact": "243041/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F17_student.png",
      "png_sha256": "607793373f0dd99b73a76ff0595b502ae29dfc6b80b8c4534d88aaf87bddb96b",
      "rgb_pixel_sha256": "3af0bf82a4b233f0a31866aa1b07d1ad9ca7feb51a82d134d404f118e29d605e",
      "actual_png_sha256": "607793373f0dd99b73a76ff0595b502ae29dfc6b80b8c4534d88aaf87bddb96b",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 2055,
      "global_seconds_exact": "137137/2000",
      "local_seconds_exact": "17137/2000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F18_student.png",
      "png_sha256": "555e48f354855f5d785d5dbf66fe481c166e1c94d7e186b4701bab0c22e66f42",
      "rgb_pixel_sha256": "add76eb6605c3b2c33f5a19ea4040b40f60ea7da78eda7982d8c1b94b5caeecf",
      "actual_png_sha256": "555e48f354855f5d785d5dbf66fe481c166e1c94d7e186b4701bab0c22e66f42",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 2069,
      "global_seconds_exact": "2071069/30000",
      "local_seconds_exact": "271069/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F19_student.png",
      "png_sha256": "b605b64522e463184a13558df65882583b8b7e783807ca9a5b610e9be87c73c3",
      "rgb_pixel_sha256": "2efa7e0edf45bc664904bc735a7ea8bbba2a6b0eb5d231100a9f8e4603000764",
      "actual_png_sha256": "b605b64522e463184a13558df65882583b8b7e783807ca9a5b610e9be87c73c3",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 2084,
      "global_seconds_exact": "521521/7500",
      "local_seconds_exact": "71521/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F20_student.png",
      "png_sha256": "eff19b8841937d46690244a4660535275c5a9f0d86f16d8c042da83500fdc622",
      "rgb_pixel_sha256": "0ff29df18a0068c83ef8c849e8ac4f57ee759371cde9df0048cd24622f201de4",
      "actual_png_sha256": "eff19b8841937d46690244a4660535275c5a9f0d86f16d8c042da83500fdc622",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 2098,
      "global_seconds_exact": "1050049/15000",
      "local_seconds_exact": "150049/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F21_student.png",
      "png_sha256": "eca6f97b18763e014d434e4434c80698710e33f458a62584dd79be18b6e1a1c6",
      "rgb_pixel_sha256": "49894285ebc3f48223db14c358051ef252c264074c71ac364b4a28322dbe54e6",
      "actual_png_sha256": "eca6f97b18763e014d434e4434c80698710e33f458a62584dd79be18b6e1a1c6",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 2112,
      "global_seconds_exact": "44044/625",
      "local_seconds_exact": "6544/625",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F22_student.png",
      "png_sha256": "0dec7077c0e3ff2387b999efae9bbf3a456e35d99be3be5a13c438d878f8ad1d",
      "rgb_pixel_sha256": "85c4674f190d6c12d016ea488cc1f998d0536f67e5a632af1d15b2bf65971132",
      "actual_png_sha256": "0dec7077c0e3ff2387b999efae9bbf3a456e35d99be3be5a13c438d878f8ad1d",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 2126,
      "global_seconds_exact": "1064063/15000",
      "local_seconds_exact": "164063/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F23_student.png",
      "png_sha256": "59bc2e3e2b3a0182a1974b1143aa07fa8e2fa4117002d3e36dbfe6d1952b3091",
      "rgb_pixel_sha256": "f20e3072e87210a6621691d1c86654864331380a9b6cc6e5c056b3d083f0b7c8",
      "actual_png_sha256": "59bc2e3e2b3a0182a1974b1143aa07fa8e2fa4117002d3e36dbfe6d1952b3091",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 2141,
      "global_seconds_exact": "2143141/30000",
      "local_seconds_exact": "343141/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F24_student.png",
      "png_sha256": "70f1a951cd4c24db1b58c69fcbec41f52d5bf14435b3daf85c3f91b0648ee76f",
      "rgb_pixel_sha256": "286913b1e081c7907031b5a6e255f18078348e0200b68e1b91b4cea3e4a284d7",
      "actual_png_sha256": "70f1a951cd4c24db1b58c69fcbec41f52d5bf14435b3daf85c3f91b0648ee76f",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 2155,
      "global_seconds_exact": "431431/6000",
      "local_seconds_exact": "71431/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F25_student.png",
      "png_sha256": "0795d55cc83a264a315a8589adc8b5f14f35166dea2cf93fd617ee127e5c2c8d",
      "rgb_pixel_sha256": "a8b838f0f2064b0d0648df3dff6d21d454fe4ff542a7e8edac18e27742f2afbf",
      "actual_png_sha256": "0795d55cc83a264a315a8589adc8b5f14f35166dea2cf93fd617ee127e5c2c8d",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 2169,
      "global_seconds_exact": "723723/10000",
      "local_seconds_exact": "123723/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F26_student.png",
      "png_sha256": "a67d4698843bd33edabbbf724aded1a7efb04d39462178acbeb2a85cc505b42c",
      "rgb_pixel_sha256": "e6f7cc3d4aad08f6f6dfe1fdeae0ba5e883ee1ad8d7d953775e20bbe1dcd246b",
      "actual_png_sha256": "a67d4698843bd33edabbbf724aded1a7efb04d39462178acbeb2a85cc505b42c",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 2183,
      "global_seconds_exact": "2185183/30000",
      "local_seconds_exact": "385183/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F27_student.png",
      "png_sha256": "dd672f357db2144f8cdfecd8228eb5850221bbb19b5d6cd013d92316c2981f20",
      "rgb_pixel_sha256": "f775e16f8f164dedd13829ee0194190e877b314dfa5a8e710dd55c4cceb1022a",
      "actual_png_sha256": "dd672f357db2144f8cdfecd8228eb5850221bbb19b5d6cd013d92316c2981f20",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 2198,
      "global_seconds_exact": "1100099/15000",
      "local_seconds_exact": "200099/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F28_student.png",
      "png_sha256": "296b284f1bad7fccaf537d5caf99a40d26db6f22992b93db352fd18b37d00aa7",
      "rgb_pixel_sha256": "fdf59d23dc3cac0a55b0a5262a095baae41f4c6df25270835c6311d90959181e",
      "actual_png_sha256": "296b284f1bad7fccaf537d5caf99a40d26db6f22992b93db352fd18b37d00aa7",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 2212,
      "global_seconds_exact": "553553/7500",
      "local_seconds_exact": "103553/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F29_student.png",
      "png_sha256": "a30663f8905de5de73fa4754991595f58c7460315622620e720bc3fa3b253321",
      "rgb_pixel_sha256": "0f2461545b0a1ad1436c8ecae07ff1772833fe812d581378a8a0121fc02271ce",
      "actual_png_sha256": "a30663f8905de5de73fa4754991595f58c7460315622620e720bc3fa3b253321",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 2226,
      "global_seconds_exact": "371371/5000",
      "local_seconds_exact": "71371/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F30_student.png",
      "png_sha256": "2413f338539387d9db3663efa8763db486acf893d5efad283fff1c0e4ee2fe09",
      "rgb_pixel_sha256": "a9ca2dd6e542abca17b73496f57588c636dbd9a002e4239ec234b6334de0aa05",
      "actual_png_sha256": "2413f338539387d9db3663efa8763db486acf893d5efad283fff1c0e4ee2fe09",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 2240,
      "global_seconds_exact": "28028/375",
      "local_seconds_exact": "5528/375",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F31_student.png",
      "png_sha256": "4c104b738be3b83a8341d4a6bda7b3a1a764be95a0a17ff915ebaf413869fb78",
      "rgb_pixel_sha256": "392bc900878219a24b2f5733cea15e14ffbede49960888574d7dd23915ca35a4",
      "actual_png_sha256": "4c104b738be3b83a8341d4a6bda7b3a1a764be95a0a17ff915ebaf413869fb78",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 2255,
      "global_seconds_exact": "451451/6000",
      "local_seconds_exact": "91451/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F32_student.png",
      "png_sha256": "69cfd9a07582e263aa2facefa1138f2e770ecc3e834bd46f50b4c5c09f79213c",
      "rgb_pixel_sha256": "609148547257adddf5529aa1d73f7277efb7f6c9d4a45fd57a828f0eb0e3f577",
      "actual_png_sha256": "69cfd9a07582e263aa2facefa1138f2e770ecc3e834bd46f50b4c5c09f79213c",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 2269,
      "global_seconds_exact": "2271269/30000",
      "local_seconds_exact": "471269/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F33_student.png",
      "png_sha256": "a1cebd3dbc5abfb27d0d7f1e128bb74c547081eeaa74192a84c761baa179f8ea",
      "rgb_pixel_sha256": "7f53ea33fef367f6244378eb644163a44f110b89a98e2b054bb94eb47b450824",
      "actual_png_sha256": "a1cebd3dbc5abfb27d0d7f1e128bb74c547081eeaa74192a84c761baa179f8ea",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 2283,
      "global_seconds_exact": "761761/10000",
      "local_seconds_exact": "161761/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F34_student.png",
      "png_sha256": "ed77be092f5efa5299dcd72092e7b766d65b57e411fcf508150c48d51faf83e9",
      "rgb_pixel_sha256": "f2ee7e39f8cd9a062f258d6f2d14b73248c871cf2e4421f0c34ba3f573cd9d48",
      "actual_png_sha256": "ed77be092f5efa5299dcd72092e7b766d65b57e411fcf508150c48d51faf83e9",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 2297,
      "global_seconds_exact": "2299297/30000",
      "local_seconds_exact": "499297/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F35_student.png",
      "png_sha256": "0ae9e0267914f6e0ff8c6fcb8a346675715c00e1f46a54fb1aa269fb34fb4828",
      "rgb_pixel_sha256": "e5d315638676b3f1c3b3f0e4b57320d6e9960292ca5b8d525bc6b067a21a1aac",
      "actual_png_sha256": "0ae9e0267914f6e0ff8c6fcb8a346675715c00e1f46a54fb1aa269fb34fb4828",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 2312,
      "global_seconds_exact": "289289/3750",
      "local_seconds_exact": "64289/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F36_student.png",
      "png_sha256": "7663491459dea2a85475e8c649b11060593e4a0bff5e34df059d53de36959f19",
      "rgb_pixel_sha256": "3a211dda41f1046fe6c067cd1ede1ea85dbe1f7f87e6b511e35ff37453f4bded",
      "actual_png_sha256": "7663491459dea2a85475e8c649b11060593e4a0bff5e34df059d53de36959f19",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 2326,
      "global_seconds_exact": "1164163/15000",
      "local_seconds_exact": "264163/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F37_student.png",
      "png_sha256": "4d34b500120f8ca2fab05937a061b643812b507f3474eabb0add472ada94613b",
      "rgb_pixel_sha256": "735dda226a962840483f23ed2d5a51be4358f630bd9bda02626072a8787f4d6a",
      "actual_png_sha256": "4d34b500120f8ca2fab05937a061b643812b507f3474eabb0add472ada94613b",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 2340,
      "global_seconds_exact": "39039/500",
      "local_seconds_exact": "9039/500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F38_student.png",
      "png_sha256": "46d2229d819f2c894238a19d89498106101d2a9f5a1092408aa62bc22982a3b9",
      "rgb_pixel_sha256": "acd14ffe34fa550ae3c6afbac982d68d6c6cda607c375bd6bcf20dfeb6e6dc61",
      "actual_png_sha256": "46d2229d819f2c894238a19d89498106101d2a9f5a1092408aa62bc22982a3b9",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 2354,
      "global_seconds_exact": "1178177/15000",
      "local_seconds_exact": "278177/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F39_student.png",
      "png_sha256": "ec4a25852e73baaf1b7b94dd81e0650043de8990ab24f8cfd40f3c05b48169bc",
      "rgb_pixel_sha256": "11f314e62612638dc349545aca3a307451bbec03a6974322c53a42cb4e9890cf",
      "actual_png_sha256": "ec4a25852e73baaf1b7b94dd81e0650043de8990ab24f8cfd40f3c05b48169bc",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 2369,
      "global_seconds_exact": "2371369/30000",
      "local_seconds_exact": "571369/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F40_student.png",
      "png_sha256": "6edc395bd41d87ed59c00e4a5a0e5a81974948932c9a671c7a2b335b82f144d1",
      "rgb_pixel_sha256": "f117a5c3d3acafdc9dbf2caa8193d7b63b7d5413ed9dc01bf9fb11af4fc86639",
      "actual_png_sha256": "6edc395bd41d87ed59c00e4a5a0e5a81974948932c9a671c7a2b335b82f144d1",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 2383,
      "global_seconds_exact": "2385383/30000",
      "local_seconds_exact": "585383/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F41_student.png",
      "png_sha256": "ef6caf9ade64205fd9fb3e66acfb31cda1b4b41df5536e1031651b144a6e4a21",
      "rgb_pixel_sha256": "4950c0002080e71735fa05b33e238714e35cda8c40c83a4ca7542e75e84d7a91",
      "actual_png_sha256": "ef6caf9ade64205fd9fb3e66acfb31cda1b4b41df5536e1031651b144a6e4a21",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 2397,
      "global_seconds_exact": "799799/10000",
      "local_seconds_exact": "199799/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F42_student.png",
      "png_sha256": "644c8bc93ccbc10a5b7aee4f93f7608596b4cba98e8ee091ff5c641763034815",
      "rgb_pixel_sha256": "3e48b53b090f273c7855fad97605857078da9c35e20fca5205276716579155fe",
      "actual_png_sha256": "644c8bc93ccbc10a5b7aee4f93f7608596b4cba98e8ee091ff5c641763034815",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 2411,
      "global_seconds_exact": "2413411/30000",
      "local_seconds_exact": "613411/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F43_student.png",
      "png_sha256": "4710e1b33ddbe61057b31ac6bb81ec8bd218d6372200b1082ed2762e72a871e1",
      "rgb_pixel_sha256": "c5ac51d74f7bfb9395887d648bf66e1ea0fcae8ee63ff7fb0c7985e6897e78e5",
      "actual_png_sha256": "4710e1b33ddbe61057b31ac6bb81ec8bd218d6372200b1082ed2762e72a871e1",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 2426,
      "global_seconds_exact": "1214213/15000",
      "local_seconds_exact": "314213/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F44_student.png",
      "png_sha256": "cc83c1d07d308d5ceafdc6511fd11550aac21a936b7d28e0eb1ff13d617cae3f",
      "rgb_pixel_sha256": "6b44991ea253d5ca90fb200c01c0ae81612e4a6b7d227fe7726b9ac9ed7c5c98",
      "actual_png_sha256": "cc83c1d07d308d5ceafdc6511fd11550aac21a936b7d28e0eb1ff13d617cae3f",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 2440,
      "global_seconds_exact": "61061/750",
      "local_seconds_exact": "16061/750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F45_student.png",
      "png_sha256": "da663965391bb772580380647fe36015d848126461e13ebca265cc5307f2204c",
      "rgb_pixel_sha256": "e043dbac01297e5e8c66a6a058c725deda5b002ab5668e9733c554ca168522ae",
      "actual_png_sha256": "da663965391bb772580380647fe36015d848126461e13ebca265cc5307f2204c",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 2454,
      "global_seconds_exact": "409409/5000",
      "local_seconds_exact": "109409/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F46_student.png",
      "png_sha256": "08e42b4d688354701dd1b2a5b8bb5eadc65080f2f08920207c120002f47b2ae7",
      "rgb_pixel_sha256": "85a9bd3de6e2b0ebdb0eddcde8208393a831d7bca7c2ab5a03cf2c8fb77b971c",
      "actual_png_sha256": "08e42b4d688354701dd1b2a5b8bb5eadc65080f2f08920207c120002f47b2ae7",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 2468,
      "global_seconds_exact": "617617/7500",
      "local_seconds_exact": "167617/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F47_student.png",
      "png_sha256": "e55be732a7a0a94411ce8312f8134603b23b773f0f34368ed32eb8c1eb6b01a5",
      "rgb_pixel_sha256": "c69991bda578a1cc4c2e353e8e3ca681d624225e57e5debaac371ddec305d91f",
      "actual_png_sha256": "e55be732a7a0a94411ce8312f8134603b23b773f0f34368ed32eb8c1eb6b01a5",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 2483,
      "global_seconds_exact": "2485483/30000",
      "local_seconds_exact": "685483/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F48_student.png",
      "png_sha256": "289513e24f47db07ca93e5212f965b280ddecd80db86b2be4fd18fab6c3283da",
      "rgb_pixel_sha256": "5da668cf6046c7e0276f1529ccd5c29d27a4820e3a2f63a3ed4770567579ceb4",
      "actual_png_sha256": "289513e24f47db07ca93e5212f965b280ddecd80db86b2be4fd18fab6c3283da",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 2497,
      "global_seconds_exact": "2499497/30000",
      "local_seconds_exact": "699497/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F49_student.png",
      "png_sha256": "f4a30bf17326026782f665b8e685775fccb8fd40c6098b1eff149ee8a2b0beb2",
      "rgb_pixel_sha256": "4a73340b3396ecd7068d34fdac627aa12f5af9237a51c7bce869b6ba54cbfd75",
      "actual_png_sha256": "f4a30bf17326026782f665b8e685775fccb8fd40c6098b1eff149ee8a2b0beb2",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 2511,
      "global_seconds_exact": "837837/10000",
      "local_seconds_exact": "237837/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F50_student.png",
      "png_sha256": "ba5846053e38e914874c34cb34fd8d1a85edbc611ba4c0e616a631507fa6e896",
      "rgb_pixel_sha256": "16d02a2dbd38a7b1c418a72eb454533cd344e1786d08fe211eb3d90973eabbfc",
      "actual_png_sha256": "ba5846053e38e914874c34cb34fd8d1a85edbc611ba4c0e616a631507fa6e896",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 2525,
      "global_seconds_exact": "101101/1200",
      "local_seconds_exact": "29101/1200",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F51_student.png",
      "png_sha256": "a104f1f36bacf1f01ed794ff02d973dfec74b2fb3035b8993ec0efa4cb023a06",
      "rgb_pixel_sha256": "08e7eee923682194f30118ae86d87fefdb25b7034a315dbb462a9bd2d03de288",
      "actual_png_sha256": "a104f1f36bacf1f01ed794ff02d973dfec74b2fb3035b8993ec0efa4cb023a06",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 2540,
      "global_seconds_exact": "127127/1500",
      "local_seconds_exact": "37127/1500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F52_student.png",
      "png_sha256": "31a1c6fbedb5195e3262afa64bb8004065d518620320d8dc469f93597151455d",
      "rgb_pixel_sha256": "77e631b21af66e20419006ee8e06cbe066c4255ded14afac695818d61e6f7b8a",
      "actual_png_sha256": "31a1c6fbedb5195e3262afa64bb8004065d518620320d8dc469f93597151455d",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 2554,
      "global_seconds_exact": "1278277/15000",
      "local_seconds_exact": "378277/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F53_student.png",
      "png_sha256": "3b3e293d70c58b49e990ec9c7edfabd1ab15ebbc280987698326843c335b3642",
      "rgb_pixel_sha256": "593c24a165eef7838eb63d2f018edeba86cc5b975d1d32875eeaa65cd9b2045e",
      "actual_png_sha256": "3b3e293d70c58b49e990ec9c7edfabd1ab15ebbc280987698326843c335b3642",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 2568,
      "global_seconds_exact": "107107/1250",
      "local_seconds_exact": "32107/1250",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F54_student.png",
      "png_sha256": "2918de78082db3ebcaadfc44d35921530d5db5f34a4d0041a37b2cceb6e79126",
      "rgb_pixel_sha256": "f5f82c35851dc89432eefe04ff5f4dad545cf2c7524672af888317c832d9be2b",
      "actual_png_sha256": "2918de78082db3ebcaadfc44d35921530d5db5f34a4d0041a37b2cceb6e79126",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 2582,
      "global_seconds_exact": "1292291/15000",
      "local_seconds_exact": "392291/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F55_student.png",
      "png_sha256": "7e8344e679dc6dd95cbac4d531cad558d4325c1e867cb66e52e8062542bfe04d",
      "rgb_pixel_sha256": "1c06bd41dc92ac8fd12f13c8c8d9e52009dba323de934345b4365a41143ac049",
      "actual_png_sha256": "7e8344e679dc6dd95cbac4d531cad558d4325c1e867cb66e52e8062542bfe04d",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 2597,
      "global_seconds_exact": "2599597/30000",
      "local_seconds_exact": "799597/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F56_student.png",
      "png_sha256": "332947e643536006aa7f8a76a534db305db496d9cedf10735d3731c84011c581",
      "rgb_pixel_sha256": "b13e8a93e1609ced4cc5dcc268e3af5dcd39345b8bc8db4ca2cc961948607304",
      "actual_png_sha256": "332947e643536006aa7f8a76a534db305db496d9cedf10735d3731c84011c581",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 2611,
      "global_seconds_exact": "2613611/30000",
      "local_seconds_exact": "813611/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F57_student.png",
      "png_sha256": "3b79800ef488cd953c2766a784fdeab64ac9fb3a4feb410167aa96a39d95d6ad",
      "rgb_pixel_sha256": "8dc31e5a7e899af56187d3b3a53c42e4387511336048dc6d3590140dc19dbee7",
      "actual_png_sha256": "3b79800ef488cd953c2766a784fdeab64ac9fb3a4feb410167aa96a39d95d6ad",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 2625,
      "global_seconds_exact": "7007/80",
      "local_seconds_exact": "2207/80",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F58_student.png",
      "png_sha256": "314bcd9bbd173a120533aa2374634da845f293d3459a924a1a300429b0ba8fb6",
      "rgb_pixel_sha256": "02846c59972a6fb57a661cac4b9211ebd379e859e41371e912098ae57fb1a67d",
      "actual_png_sha256": "314bcd9bbd173a120533aa2374634da845f293d3459a924a1a300429b0ba8fb6",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 2639,
      "global_seconds_exact": "2641639/30000",
      "local_seconds_exact": "841639/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F59_student.png",
      "png_sha256": "8914301a0ab8fe5e83716522342958a1ef9ad140f30b21a18e5d29111b60b05a",
      "rgb_pixel_sha256": "37f4377ed83c46f40c4d73c71b0f23ac8ae0a89880f12f39ab7e5b663834a202",
      "actual_png_sha256": "8914301a0ab8fe5e83716522342958a1ef9ad140f30b21a18e5d29111b60b05a",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 2654,
      "global_seconds_exact": "1328327/15000",
      "local_seconds_exact": "428327/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F60_student.png",
      "png_sha256": "78c3a4aa16be2f08f0c3d294f5616ae0e1f1e360fc5d2cfdf7492806c0af8699",
      "rgb_pixel_sha256": "ef818d4445a9b4b24a1d309a29d44cb0be1d4d30ee23c4565805ec3b787b20a0",
      "actual_png_sha256": "78c3a4aa16be2f08f0c3d294f5616ae0e1f1e360fc5d2cfdf7492806c0af8699",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 2668,
      "global_seconds_exact": "667667/7500",
      "local_seconds_exact": "217667/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F61_student.png",
      "png_sha256": "f42aa737e6131725e494d4c7d23c5a710328e2a8308e340dbd46505f3053347b",
      "rgb_pixel_sha256": "0eb3a81083bdab38b05fcc5a28d92ac5b9dd8fd5559a17e7a4ccc9c50b026f32",
      "actual_png_sha256": "f42aa737e6131725e494d4c7d23c5a710328e2a8308e340dbd46505f3053347b",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 2682,
      "global_seconds_exact": "447447/5000",
      "local_seconds_exact": "147447/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F62_student.png",
      "png_sha256": "91587d583090a30fa2ced1c50021ad967bd5d33a241f59454b1c0a5985f1a67b",
      "rgb_pixel_sha256": "c4f72e1a25957ba00d8b08f3b0e7e97153b4954472671e5b8d6bd0bb381bd8e1",
      "actual_png_sha256": "91587d583090a30fa2ced1c50021ad967bd5d33a241f59454b1c0a5985f1a67b",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 2697,
      "global_seconds_exact": "899899/10000",
      "local_seconds_exact": "299899/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\01_kLxoNp-UchI_W02\\student_views\\F63_student.png",
      "png_sha256": "5fb653b3cdb16f01ea65f7d5e2300d0866a7cdde785dd0c1981fd2348dddba0d",
      "rgb_pixel_sha256": "e9ad90fcd6e8cd342df3921816c9cb65c046717a37f6193c6771580a44f9b2af",
      "actual_png_sha256": "5fb653b3cdb16f01ea65f7d5e2300d0866a7cdde785dd0c1981fd2348dddba0d",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    }
  ]
}



## 完整新增公开证据：01_kLxoNp-UchI_W02.independent_student_view_review_v1.md
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\01_kLxoNp-UchI_W02.independent_student_view_review_v1.md
字节：1199；SHA256：e04c72ade362f316e44a1ae678ce7054c8b70c5baf12eb0c9d535770d5031816

# kLxoNp-UchI:SLOT6:2 有效视图独立续审

已通过view_image读完64张实际本地CPU tensor重构PNG（8批），全部SHA与receipt相符，source ordinal及exact PTS与初稿逐项一致。初稿引用SHA：e9a6402f66c5b5e6adb1ce7a8525bdefab9e6b2572f26f0f261baf14e643ef42。

640x352有效显示保留草地侧卧脸、低头走近、侧脸转头/眼睑与末端卧犬结果。F25-F28与F34-F39仍严重失焦；F29-F33仍不足确定独立姿态动作类别。不能由processor重构补回原失焦证据。原K/NO/U不变。

K/NO/U无变更；原具体UNKNOWN保留。未决问题影响完整窗口目标：切点、严重失焦与短爪位变化区间保留具体U，可能影响独立事件选择或清晰段边界；稳定可见重复间隙未扩大U。 对应帧：F02, F03, F17, F18, F25, F26, F27, F28, F29, F30, F31, F32, F33, F34, F35, F36, F37, F38, F39, F54, F55, F56, F57, F58, F59, F60, F61。

student_processor_visibility_verified=true（仅本地CPU实际显示视图）；Linux execution=false；training_admitted=false；full_native_frames_observed=false；full_window_target_admitted=false。仍未接收或读取教师内容；可见性不是完整训练资格。



## 完整新增公开证据：proposal.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\02_AwmHb44_ouw_W10\teacher_attempt01_http1\proposal.json
字节：23953；SHA256：bf26a73380aeb0a8fe1acdea44f11f16de034832100cab558851437c93fd4c17

{
  "window_id": "AwmHb44_ouw:SLOT6:10",
  "source_sha256": "82ecca1de0363253060bb3c19e2f5dbd4080bfc0cd790db23c3e73ffd76a602f",
  "clip_sha256": "43bad39a327e33bfc4b7a82966f95eed56a7a0e46405e3f2b18e1b5c427ff1a1",
  "model": "Gemini 3.8 Flash (High)",
  "native_video_actual_scope": "Tool view_file decoded clip.mp4 using internal opaque temporal sampling at 1 fps (30 frames sampled from 00:00 to 00:29), providing a coarse timeline overview rather than complete frame-by-frame observation. Full native evaluation is strictly grounded on the 64 discrete native RGB frame PNGs (F00-F63, local pts 0.033s to 29.996s) and 8 reconstructed student view PNGs.",
  "full_native_frames_observed": false,
  "frame_observations": [
    {
      "frame_id": "F00",
      "source_ordinal": 8992,
      "local_seconds_exact": "62/1875",
      "observed": true,
      "visible_fact": "手部按在轮胎轮毂中心气门嘴位置的近距离特写展示，背景为水泥地面。"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 9006,
      "local_seconds_exact": "2501/5000",
      "observed": true,
      "visible_fact": "手部持续按压在轮毂中央气门嘴/螺栓处，特写景别与姿势保持一致。"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 9020,
      "local_seconds_exact": "1451/1500",
      "observed": true,
      "visible_fact": "手部持续按压检查气门嘴，手部轻微调整受力状态。"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 9034,
      "local_seconds_exact": "21517/15000",
      "observed": true,
      "visible_fact": "手部按在气门嘴上，近距离特写展示气门嘴安装及固定状态。"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 9049,
      "local_seconds_exact": "58049/30000",
      "observed": true,
      "visible_fact": "手部按住气门嘴特写镜头的末尾帧，保持特写展示状态。"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 9063,
      "local_seconds_exact": "24021/10000",
      "observed": true,
      "visible_fact": "镜头切换至俯视中全景，组装好的越野车轮平放在水泥地上，右侧摆放白色喷雾瓶、活动扳手及红色工具箱。"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 9077,
      "local_seconds_exact": "86077/30000",
      "observed": true,
      "visible_fact": "俯视固定镜头，车轮、喷雾瓶、扳手和红色工具箱静止放置，无动作发生。"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 9091,
      "local_seconds_exact": "100091/30000",
      "observed": true,
      "visible_fact": "俯视固定镜头，车轮与周边工具保持完全静止状态。"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9106,
      "local_seconds_exact": "57553/15000",
      "observed": true,
      "visible_fact": "俯视静止展示车轮、喷雾瓶、活动扳手及红色工具箱。"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 9120,
      "local_seconds_exact": "538/125",
      "observed": true,
      "visible_fact": "俯视固定镜头持续展示静置的车轮与检修工具。"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 9134,
      "local_seconds_exact": "71567/15000",
      "observed": true,
      "visible_fact": "俯视固定镜头持续展示静止车轮与工具，无人员入镜。"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 9148,
      "local_seconds_exact": "39287/7500",
      "observed": true,
      "visible_fact": "车轮、白色喷雾瓶、扳手及红色铁工具箱静止放置于地面。"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 9163,
      "local_seconds_exact": "172163/30000",
      "observed": true,
      "visible_fact": "俯视全景持续展示静置状态的装配轮胎与工具。"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 9177,
      "local_seconds_exact": "62059/10000",
      "observed": true,
      "visible_fact": "俯视镜头保持静止，画面无任何动态位移。"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 9191,
      "local_seconds_exact": "200191/30000",
      "observed": true,
      "visible_fact": "车轮与工具静止陈列于水泥地面。"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 9205,
      "local_seconds_exact": "42841/6000",
      "observed": true,
      "visible_fact": "俯视固定视角，持续展示组装完成的车轮及检修工具。"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 9220,
      "local_seconds_exact": "11461/1500",
      "observed": true,
      "visible_fact": "俯视固定视角，车轮与工具布局无变化。"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 9234,
      "local_seconds_exact": "40539/5000",
      "observed": true,
      "visible_fact": "俯视固定视角，车轮与工具完全静止。"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 9248,
      "local_seconds_exact": "16078/1875",
      "observed": true,
      "visible_fact": "俯视固定视角，持续展示静止的轮胎成果及配套工具。"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 9262,
      "local_seconds_exact": "135631/15000",
      "observed": true,
      "visible_fact": "俯视固定视角，展示静止状态的装配车轮。"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 9277,
      "local_seconds_exact": "286277/30000",
      "observed": true,
      "visible_fact": "俯视固定视角，地面车轮、喷雾瓶、扳手、工具箱保持静止。"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 9291,
      "local_seconds_exact": "100097/10000",
      "observed": true,
      "visible_fact": "俯视固定视角，场景持续静止无交互。"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 9305,
      "local_seconds_exact": "62861/6000",
      "observed": true,
      "visible_fact": "俯视固定视角，车轮与工具静置展示。"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 9319,
      "local_seconds_exact": "328319/30000",
      "observed": true,
      "visible_fact": "俯视静物镜头最后一帧，车轮与工具保持原位静止。"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 9334,
      "local_seconds_exact": "171667/15000",
      "observed": true,
      "visible_fact": "镜头切换至自拍人像特写，灰白短发、留八字胡的中年男子面向镜头讲话，背景为木栅栏与白色平房。"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 9348,
      "local_seconds_exact": "29779/2500",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话，嘴唇微动。"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 9362,
      "local_seconds_exact": "185681/15000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，视线正视镜头方向。"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 9376,
      "local_seconds_exact": "24086/1875",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话，神态自然微动。"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 9391,
      "local_seconds_exact": "400391/30000",
      "observed": true,
      "visible_fact": "中年男子口述讲话，头部微有轻微晃动。"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 9405,
      "local_seconds_exact": "27627/2000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话，口型处于张开状态。"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 9419,
      "local_seconds_exact": "428419/30000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话，背景木栅栏与房屋保持静止。"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 9433,
      "local_seconds_exact": "442433/30000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话特写。"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 9448,
      "local_seconds_exact": "57181/3750",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话，口型微变。"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 9462,
      "local_seconds_exact": "78577/5000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，口型开合。"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 9476,
      "local_seconds_exact": "121369/7500",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头口述。"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 9490,
      "local_seconds_exact": "49949/3000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话，表情随发音微调。"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 9505,
      "local_seconds_exact": "102901/6000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，人脸正面特写。"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 9519,
      "local_seconds_exact": "176173/10000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，嘴形张开。"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 9533,
      "local_seconds_exact": "542533/30000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 9547,
      "local_seconds_exact": "556547/30000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，头部位置基本恒定。"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 9562,
      "local_seconds_exact": "285781/15000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头口述，神态自若。"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 9576,
      "local_seconds_exact": "24399/1250",
      "observed": true,
      "visible_fact": "中年男子持续讲话，嘴形变化。"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 9590,
      "local_seconds_exact": "59959/3000",
      "observed": true,
      "visible_fact": "中年男子面向镜头讲话，眼神直视拍摄设备。"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 9604,
      "local_seconds_exact": "153401/7500",
      "observed": true,
      "visible_fact": "中年男子持续讲话，口型开合。"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 9619,
      "local_seconds_exact": "628619/30000",
      "observed": true,
      "visible_fact": "中年男子持续口述讲话。"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 9633,
      "local_seconds_exact": "214211/10000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，面部表情微动。"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 9647,
      "local_seconds_exact": "656647/30000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 9661,
      "local_seconds_exact": "670661/30000",
      "observed": true,
      "visible_fact": "中年男子持续口述讲话，背景平房和树木静止。"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 9676,
      "local_seconds_exact": "171419/7500",
      "observed": true,
      "visible_fact": "中年男子讲话人特写，口型变化。"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 9690,
      "local_seconds_exact": "23323/1000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 9704,
      "local_seconds_exact": "89213/3750",
      "observed": true,
      "visible_fact": "中年男子持续口述讲话，神态专注。"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 9718,
      "local_seconds_exact": "363859/15000",
      "observed": true,
      "visible_fact": "中年男子持续讲话，嘴形开合。"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 9733,
      "local_seconds_exact": "742733/30000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 9747,
      "local_seconds_exact": "252249/10000",
      "observed": true,
      "visible_fact": "中年男子口述讲话，面部特写。"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 9761,
      "local_seconds_exact": "770761/30000",
      "observed": true,
      "visible_fact": "中年男子持续面向镜头讲话。"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 9775,
      "local_seconds_exact": "31391/1200",
      "observed": true,
      "visible_fact": "中年男子持续讲话，嘴型张开。"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 9790,
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
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\02_AwmHb44_ouw_W10.independent_initial_blind_v1.md
字节：2526；SHA256：7ff060be87edaaf0ac3102db376c5c17c3a6e8f0c5bc71f18acdd42779ed598e

# AwmHb44_ouw:SLOT6:10 独立初始盲审

实际通过 view_image 读取 F00–F63 全部64张原始 PNG（8批，每批8张）；PNG SHA 全部与 manifest 匹配。仅使用本窗 manifest/frames，未读教师内容、旧标签、分数、模型预测、其他项目文件、overview、视频或音频。

声明窗口：300 — 330 秒（源全局时钟）。K=2 段，NO=1 段，U=3 段；三类按半开区间互斥覆盖。以下是初步编辑建议，切点与失焦、无音频问题在 U 中保留。

| 类别 | 全局精确秒区间 | 建议/事实 | 理由 |
|---|---|---|---|
| K | 300 → 9058049/30000 | 手与轮圈内侧小凸点的操作细节 | 近距离展示手指与轮圈内侧的接触关系和构造细节，有技术过程镜头价值；具体用途未确认。 |
| U | 9058049/30000 → 3024021/10000 | 操作近景到地面轮胎全景的切点 | 手消失并换全景，切点未知；接触后的机械结果未见。 |
| K | 3024021/10000 → 38038/125 | 轮胎、轮圈与相邻工具的全景 | 轮胎平放、轮圈朝上、白喷瓶和可调扳手的位置清楚，可作短建立/状态镜头；不声称修好或工具已使用。 |
| NO | 38038/125 → 9328319/30000 | 同一轮胎工具布局的重复持留 | 物品静态关系已建立，后续样本仅轻微机位变化，未见操作或新结果。 |
| U | 9328319/30000 → 4671667/15000 | 工具布局到人物面部镜头的切点 | 主体变化，切点未知。 |
| U | 4671667/15000 → 330 | 连续人物近景的讲述意义 | 嘴型持续变化，可能有与过程相关的关键说明；没有音频/转录，不能确认说了什么，也不能默认全部人物近景为NO。视觉上未见手势、工具操作或新结果。 |

未决事实：

- 轮圈内侧小凸点的具体功能、手是否完成旋紧/释放/测试未能确认；K只指可见接触细节。
- 喷瓶、扳手、工具盒存在不证明实际使用；静态全景不证明修复成功。
- 人物近景的解释内容及其在编辑中的必要性需要音频或独立授权的对应内容证据。

每帧 frame_id、source_ordinal、exact PTS、PNG路径/期望与实际SHA、读图批次和事实见同名 JSON。有限floor64采样可能漏掉瞬时动作，稳定重复间隙没有机械转成U。源视频/完整native帧和实际processor有效视图未见。

student_processor_visibility_verified=false；training_admitted=false；full_native_frames_observed=false。这是独立初始盲审，不是金标或完整训练资格。



## 完整新增公开证据：02_AwmHb44_ouw_W10.independent_student_view_review_v1.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\02_AwmHb44_ouw_W10.independent_student_view_review_v1.json
字节：54960；SHA256：a736f675f96bcd94958c9123cb629a1aa2db8e71da4f476a78dee746961d8f74

{
  "schema": "independent_student_effective_view_blind_review_v1",
  "review_utc": "2026-10-10 06:37:01 UTC",
  "window_id": "AwmHb44_ouw:SLOT6:10",
  "prior_initial_review": {
    "path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/blind_reviews/initial/02_AwmHb44_ouw_W10.independent_initial_blind_v1.json",
    "sha256": "a8b6e30dcc4fdd79fe4ef53bc6b2f7605ae06616d62aa9c7faaad9c56e46904d",
    "bytes_preserved": true
  },
  "student_processor_visibility_verified": true,
  "student_visibility_verification_scope": "ALL_64_ACTUAL_LOCAL_CPU_TENSOR_RECONSTRUCTED_PNGS_VISUALLY_READ; Linux processor execution not verified",
  "training_admitted": false,
  "full_native_frames_observed": false,
  "full_window_target_admitted": false,
  "blind_attestation": {
    "teacher_content_received": false,
    "teacher_files_read": false,
    "old_labels_or_scores_or_model_predictions_read": false,
    "network_model_GPU_used": false
  },
  "machine_receipt": {
    "path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/observations/02_AwmHb44_ouw_W10/student_views/receipt.json",
    "sha256": "150d393e9cd5301cdbc645166feea3cd1e398c1a77742f06f0ecc824f561d4c7",
    "status": "PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS",
    "manifest_sha256": "838b7362c8061f824e1ccc79059ba3406185eff9143ef2ec303e9f3bef8c0a52",
    "processor_binding_sha256": "272ab26a6dc9bbe42db40531eec316f91aed5f4073b6ab9d79a2aa80d1294c29",
    "runtime_sha256": "73f014e20034e0c61e9d57fe927ec7c69392f2d5f5e7a2f3f9f06ca6efa614b9",
    "decoder_sha256": "7b79a6713e3a406d015bc546fc45ce6172b7cf8d3967592779bfdd8c23a6fe09",
    "normalized_tensor_sha256": "c0f0456b995aa5d2cf14d4417ff94c49b1097626660f34c86cb60a7da34c4196",
    "actual_tensor_shape": [
      23936,
      1536
    ],
    "video_grid_thw": [
      [
        32,
        22,
        34
      ]
    ],
    "patch_inverse_exact": true,
    "torch_version": "2.5.1+cpu",
    "transformers_version": "4.57.1",
    "linux_execution": false,
    "new_model_calls": 0,
    "new_optimizer_updates": 0,
    "rendered_view": "Inverse patch rearrangement, inverse normalization, rounded uint8 PNG. Display reconstruction; normalized model tensor SHA bound separately."
  },
  "actual_viewing": {
    "frames": 64,
    "batches": 13,
    "batch_size": "F00-F23每批8张；F24-F63每批4张",
    "all_png_sha_match_receipt": true,
    "all_source_ordinals_and_exact_PTS_match_initial_manifest": true,
    "width": 544,
    "height": 352
  },
  "visibility_changes_and_learnability": "544x352有效显示仍见F00-F04手指接触轮圈内侧点，但点的功能或完成操作不可判。F05-F23轮胎/喷瓶/扳手布局可辨。F24-F63人物嘴型与背景可见，本轮未提供音频证据，讲述意义未知不变。原K/NO/U不变。",
  "K_NO_U_changed": false,
  "label_changes": [],
  "retained_segments": [
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
  "unresolved_for_full_window": {
    "frames": [
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
    ],
    "issue": "连续人物讲述意义未知，且F00-F04接触点的机械功能/结果未知；不确认台词、工具使用或修复成功。影响完整窗口目标。",
    "affects_full_window_target": true
  },
  "limitations": [
    "有效视图是inverse patch及inverse normalization后round uint8的显示重构；不能把PNG字节等同于归一化model tensor。tensor SHA与机器回执独立绑定。",
    "所有64采样视图已看，但完整native帧未看，具体切点和识别不清事件保留U。",
    "processor文件SHA与Linux实际元数据回执绑定，不证明Linux已经运行相同processor。",
    "可见性通过不等于训练准入、金标或冻结完整窗口目标。"
  ],
  "student_view_inventory": [
    {
      "frame_id": "F00",
      "source_ordinal": 8992,
      "global_seconds_exact": "562562/1875",
      "local_seconds_exact": "62/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F00_student.png",
      "png_sha256": "e3fd35951100af90f0d901327fd10a818ad43050d80be2b8d0788a305eb8f45b",
      "rgb_pixel_sha256": "ada38f2e82a364ab82e580474e2f4370906cd0e4ca9aa1f539a94a05284f0b22",
      "actual_png_sha256": "e3fd35951100af90f0d901327fd10a818ad43050d80be2b8d0788a305eb8f45b",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 9006,
      "global_seconds_exact": "1502501/5000",
      "local_seconds_exact": "2501/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F01_student.png",
      "png_sha256": "8f5b75f34a61a1fee01606cb1a6e284f69b79b07e70dd693d288512410a80aa8",
      "rgb_pixel_sha256": "fb40ec9f0c6272e2bca8734a4a521b3267fc2632a887062d5fe3c971b601645c",
      "actual_png_sha256": "8f5b75f34a61a1fee01606cb1a6e284f69b79b07e70dd693d288512410a80aa8",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 9020,
      "global_seconds_exact": "451451/1500",
      "local_seconds_exact": "1451/1500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F02_student.png",
      "png_sha256": "3fc964d31198dc6603a337b48ad281695bd151eb502ecebcb9266b586838bee6",
      "rgb_pixel_sha256": "317e563a10ec5e7ef7d5f8284bb46b02b45c959b13a43b902d392280026af45f",
      "actual_png_sha256": "3fc964d31198dc6603a337b48ad281695bd151eb502ecebcb9266b586838bee6",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 9034,
      "global_seconds_exact": "4521517/15000",
      "local_seconds_exact": "21517/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F03_student.png",
      "png_sha256": "19df88f832e6f30f10ca128cf4194a3cbaaa89c0404556548dd40cba6ec93c45",
      "rgb_pixel_sha256": "5de196b442e6da02f2d42d2c6dfb1d28651c0073a57d3b3ac8dba66ae82972d0",
      "actual_png_sha256": "19df88f832e6f30f10ca128cf4194a3cbaaa89c0404556548dd40cba6ec93c45",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 9049,
      "global_seconds_exact": "9058049/30000",
      "local_seconds_exact": "58049/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F04_student.png",
      "png_sha256": "7495583ada71e2a37c515cb80c508fec6a34d7b5d5616698b47d65a1f418c7f7",
      "rgb_pixel_sha256": "5b5d15c6597504b2fa22e46a0fd6ca3c0477799e74a9c73e90165afd966c6810",
      "actual_png_sha256": "7495583ada71e2a37c515cb80c508fec6a34d7b5d5616698b47d65a1f418c7f7",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 9063,
      "global_seconds_exact": "3024021/10000",
      "local_seconds_exact": "24021/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F05_student.png",
      "png_sha256": "b30ccf31a421fdc8bc2eed63a26706516d6737d6f64cbd61bd4258625468f7dd",
      "rgb_pixel_sha256": "a27e260d9f2e2fd6f5c89f732f55f4ed675326ce125ee99a2d991cbc5c8ad052",
      "actual_png_sha256": "b30ccf31a421fdc8bc2eed63a26706516d6737d6f64cbd61bd4258625468f7dd",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 9077,
      "global_seconds_exact": "9086077/30000",
      "local_seconds_exact": "86077/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F06_student.png",
      "png_sha256": "c8e02385c12b8eb5e53a56807e7acfc9899bd5b1058877c09c725cecf1f32cae",
      "rgb_pixel_sha256": "0e1a6da9240608a29ca3f13cf3a372d4bda0d83373aa7616dbc10f82aef5a5c3",
      "actual_png_sha256": "c8e02385c12b8eb5e53a56807e7acfc9899bd5b1058877c09c725cecf1f32cae",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 9091,
      "global_seconds_exact": "9100091/30000",
      "local_seconds_exact": "100091/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F07_student.png",
      "png_sha256": "eb082027a95d4d36b14965aeaeba94144fcb79c9038dd517124e0172c51c51f7",
      "rgb_pixel_sha256": "6d8f24db462c1badbfdf92a34d4d9708994ef8b2ab1f88a132cfec58362da5bf",
      "actual_png_sha256": "eb082027a95d4d36b14965aeaeba94144fcb79c9038dd517124e0172c51c51f7",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9106,
      "global_seconds_exact": "4557553/15000",
      "local_seconds_exact": "57553/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F08_student.png",
      "png_sha256": "72641919c9de75583f144f3743a38091183f58dd75fe5b001718ed12a2cba56e",
      "rgb_pixel_sha256": "e8d637230e801eced39d05cb65a5a844fc85abb97d82ae660bb1104abe926e8f",
      "actual_png_sha256": "72641919c9de75583f144f3743a38091183f58dd75fe5b001718ed12a2cba56e",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 9120,
      "global_seconds_exact": "38038/125",
      "local_seconds_exact": "538/125",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F09_student.png",
      "png_sha256": "1880d23908a65209ccf076f73f442fe39cffd218e289d6ac5531a5f9f08aea78",
      "rgb_pixel_sha256": "6eff42614ac07752ad63c9efe6a53eec8f59476629d15e7a664de2157d145e78",
      "actual_png_sha256": "1880d23908a65209ccf076f73f442fe39cffd218e289d6ac5531a5f9f08aea78",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 9134,
      "global_seconds_exact": "4571567/15000",
      "local_seconds_exact": "71567/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F10_student.png",
      "png_sha256": "f3692630038f0652f8ffb6c27214455566b09ec7abed33361c9019b80ff43db6",
      "rgb_pixel_sha256": "ab56d653d120acb14b10515d54c89beb1039a04f80b87798ea617cd712d32d6b",
      "actual_png_sha256": "f3692630038f0652f8ffb6c27214455566b09ec7abed33361c9019b80ff43db6",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 9148,
      "global_seconds_exact": "2289287/7500",
      "local_seconds_exact": "39287/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F11_student.png",
      "png_sha256": "3d627cd8d2f87b678f0b0efd98a95cd183cf1e5ddd5aa13e5ddd2101e170a083",
      "rgb_pixel_sha256": "554be981fb03c9c1204de697f3c8ecb4378019dd4bd33fe4bf139ac30175ee9c",
      "actual_png_sha256": "3d627cd8d2f87b678f0b0efd98a95cd183cf1e5ddd5aa13e5ddd2101e170a083",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 9163,
      "global_seconds_exact": "9172163/30000",
      "local_seconds_exact": "172163/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F12_student.png",
      "png_sha256": "c8be1685f93e3ef16bbd612c9cb8aff4f4f8eaa3083ee64fd5ce2ac8542dae42",
      "rgb_pixel_sha256": "588165abfdfd79f1b8885aded5fba66812ac24efecb0cb8683cb61c7bf2244e4",
      "actual_png_sha256": "c8be1685f93e3ef16bbd612c9cb8aff4f4f8eaa3083ee64fd5ce2ac8542dae42",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 9177,
      "global_seconds_exact": "3062059/10000",
      "local_seconds_exact": "62059/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F13_student.png",
      "png_sha256": "460753b711d7e884a08303fd322f854db4f8b70ae36506a7e7134987d8d08aee",
      "rgb_pixel_sha256": "2f252c629b5602e4ec5ea6061db13db03f069d1ce1ef401a70ab601d6b8a3cbb",
      "actual_png_sha256": "460753b711d7e884a08303fd322f854db4f8b70ae36506a7e7134987d8d08aee",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 9191,
      "global_seconds_exact": "9200191/30000",
      "local_seconds_exact": "200191/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F14_student.png",
      "png_sha256": "6e13245db26a6751efc4688d1410ffb75d223df175ba8fdadf217b58142fd15f",
      "rgb_pixel_sha256": "364e6a71d4b2d31cba7ad2e19723e39d25886fcabaa56511987e3aeac40188e3",
      "actual_png_sha256": "6e13245db26a6751efc4688d1410ffb75d223df175ba8fdadf217b58142fd15f",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 9205,
      "global_seconds_exact": "1842841/6000",
      "local_seconds_exact": "42841/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F15_student.png",
      "png_sha256": "25db6a5ac0b04cbaa353a8aa175cb918adb052e1a1cd4989ab436f353384e0dc",
      "rgb_pixel_sha256": "6f23b5b55b1646d56417ee9cc3cce4dc89f81a265215db68c2b877716e46544e",
      "actual_png_sha256": "25db6a5ac0b04cbaa353a8aa175cb918adb052e1a1cd4989ab436f353384e0dc",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 9220,
      "global_seconds_exact": "461461/1500",
      "local_seconds_exact": "11461/1500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F16_student.png",
      "png_sha256": "e844bb62df475ebed633774e90ac308616d60b994c283c33794ead03dfd96b23",
      "rgb_pixel_sha256": "6a5b6f91aae4cd38ecf9383fa4f46507fe90613111ac55a85b71d69dec181481",
      "actual_png_sha256": "e844bb62df475ebed633774e90ac308616d60b994c283c33794ead03dfd96b23",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 9234,
      "global_seconds_exact": "1540539/5000",
      "local_seconds_exact": "40539/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F17_student.png",
      "png_sha256": "247848629a08d69b3dcc8b9d95436f65e92d2efa10a93fe6ccf02710c9d0b42a",
      "rgb_pixel_sha256": "20fd61a9a553cb39511760c3c128c3434f68517c6e5fc351aad4264aed87833b",
      "actual_png_sha256": "247848629a08d69b3dcc8b9d95436f65e92d2efa10a93fe6ccf02710c9d0b42a",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 9248,
      "global_seconds_exact": "578578/1875",
      "local_seconds_exact": "16078/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F18_student.png",
      "png_sha256": "b6d47935a262ebfe6c1830f62d4cf6b614eaff2cbf0b7878b4b3cd12625ed4aa",
      "rgb_pixel_sha256": "9223c9315aec2e1988ee545c7387da5ec93f56052e231158a68abf644ac6a3c3",
      "actual_png_sha256": "b6d47935a262ebfe6c1830f62d4cf6b614eaff2cbf0b7878b4b3cd12625ed4aa",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 9262,
      "global_seconds_exact": "4635631/15000",
      "local_seconds_exact": "135631/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F19_student.png",
      "png_sha256": "16c5c6068cda9f35185dec86fd6534832e546c7b891f8f109354e1ced6779286",
      "rgb_pixel_sha256": "79013d1e11ad34c92d073609385d525ee53110f057ca192439ac4b6e67617e1d",
      "actual_png_sha256": "16c5c6068cda9f35185dec86fd6534832e546c7b891f8f109354e1ced6779286",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 9277,
      "global_seconds_exact": "9286277/30000",
      "local_seconds_exact": "286277/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F20_student.png",
      "png_sha256": "4be019f4179e555bd04e8a5ecf9263f48a7db080de28c55ebc5a3b0e8e456209",
      "rgb_pixel_sha256": "b4da3dc307627fec651cfd494e5368c4aa323ee6a69ab680509abe128c9b5149",
      "actual_png_sha256": "4be019f4179e555bd04e8a5ecf9263f48a7db080de28c55ebc5a3b0e8e456209",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 9291,
      "global_seconds_exact": "3100097/10000",
      "local_seconds_exact": "100097/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F21_student.png",
      "png_sha256": "983a62acf551f0f5d01a38f0654f1955aecebe1acd229a6a062c8cd21948db9b",
      "rgb_pixel_sha256": "ff210619d78077b78019881ad4a0c8c7b440ef8bc254bbe3a3a3b7924739dafd",
      "actual_png_sha256": "983a62acf551f0f5d01a38f0654f1955aecebe1acd229a6a062c8cd21948db9b",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 9305,
      "global_seconds_exact": "1862861/6000",
      "local_seconds_exact": "62861/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F22_student.png",
      "png_sha256": "e3ffd96457dff4acaccaefc0d191f5557c686c9d180038cd514b727e54843a90",
      "rgb_pixel_sha256": "465e59d05b0c07af3991cc65dead21e9deb2c6c1882291b288089e18f4f9e2d4",
      "actual_png_sha256": "e3ffd96457dff4acaccaefc0d191f5557c686c9d180038cd514b727e54843a90",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 9319,
      "global_seconds_exact": "9328319/30000",
      "local_seconds_exact": "328319/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F23_student.png",
      "png_sha256": "def2dedd89819b82813ac905f79689633b00f6709d2e48cd3131113fabc5d590",
      "rgb_pixel_sha256": "6a82949e0f69d9b940ee44e951d743861ae218359c302657d850233cbf885559",
      "actual_png_sha256": "def2dedd89819b82813ac905f79689633b00f6709d2e48cd3131113fabc5d590",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 9334,
      "global_seconds_exact": "4671667/15000",
      "local_seconds_exact": "171667/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F24_student.png",
      "png_sha256": "df28c8165099a5686a753ba794af7e4d512e577c255020ea905d42f1c669722f",
      "rgb_pixel_sha256": "a54d0b945fd288d8781036e3109140af1d847b57f329410cf35dc45f79288a48",
      "actual_png_sha256": "df28c8165099a5686a753ba794af7e4d512e577c255020ea905d42f1c669722f",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 9348,
      "global_seconds_exact": "779779/2500",
      "local_seconds_exact": "29779/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F25_student.png",
      "png_sha256": "f1f41073ad54949af28dff78008f00c2957de7ae5fb7ed422b01e972ca5bcaaa",
      "rgb_pixel_sha256": "d5faca01e6cc96f8d9d1e7db3133a78142e1171082a997361d12f44a0562450e",
      "actual_png_sha256": "f1f41073ad54949af28dff78008f00c2957de7ae5fb7ed422b01e972ca5bcaaa",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 9362,
      "global_seconds_exact": "4685681/15000",
      "local_seconds_exact": "185681/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F26_student.png",
      "png_sha256": "301a993840fd9c72a713043f3816945a7c071248616814185a05530c7c97efc6",
      "rgb_pixel_sha256": "ee33fe95364e7cc99d9b937f4d47fc5babd4405c6be2f5c325989dc76daca1eb",
      "actual_png_sha256": "301a993840fd9c72a713043f3816945a7c071248616814185a05530c7c97efc6",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 9376,
      "global_seconds_exact": "586586/1875",
      "local_seconds_exact": "24086/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F27_student.png",
      "png_sha256": "f37426b1cd3d3b5e53ee4f2d2f04143afe5f146d8023808b9e0e82e8c0a7025e",
      "rgb_pixel_sha256": "3c48560cd0b39d1247836cead25f40104a49b5435657bc384b077bcb92b8cdf2",
      "actual_png_sha256": "f37426b1cd3d3b5e53ee4f2d2f04143afe5f146d8023808b9e0e82e8c0a7025e",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 9391,
      "global_seconds_exact": "9400391/30000",
      "local_seconds_exact": "400391/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F28_student.png",
      "png_sha256": "075a13ad7eeef960905b6e02aad805800b49ae783b107c796c4706b8591038a8",
      "rgb_pixel_sha256": "490c1cd9bd738da3fdf5d55f6235b4acc8245625977d9bde86f69204f7d3198a",
      "actual_png_sha256": "075a13ad7eeef960905b6e02aad805800b49ae783b107c796c4706b8591038a8",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 9405,
      "global_seconds_exact": "627627/2000",
      "local_seconds_exact": "27627/2000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F29_student.png",
      "png_sha256": "9163f71ba7d0b3aa6f9c523ad1001f533c88fc306e7326c33f67464bc83a6457",
      "rgb_pixel_sha256": "f77db83b1d72e62ccab82f69d985e3018bf7e18412cc7b3b0ce1ad1bd510aeb4",
      "actual_png_sha256": "9163f71ba7d0b3aa6f9c523ad1001f533c88fc306e7326c33f67464bc83a6457",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 9419,
      "global_seconds_exact": "9428419/30000",
      "local_seconds_exact": "428419/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F30_student.png",
      "png_sha256": "b5290f3da1da17ee8b96e7712cde05e9d4989c9a656f2cc9cc654c5323d0358d",
      "rgb_pixel_sha256": "0b3cbd35b97f036a16d3fdbe2d1eea884c3b4c1a6823015e48bd02bd451b21d8",
      "actual_png_sha256": "b5290f3da1da17ee8b96e7712cde05e9d4989c9a656f2cc9cc654c5323d0358d",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 9433,
      "global_seconds_exact": "9442433/30000",
      "local_seconds_exact": "442433/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F31_student.png",
      "png_sha256": "d0907c152c2144579e1f3c2462379f35be0a3a6cb2e78506b25d1f3ee39b825e",
      "rgb_pixel_sha256": "d116c425d520acd2e28a0bedd68f70aed53b077c46332203fa5618a3a1e93a9f",
      "actual_png_sha256": "d0907c152c2144579e1f3c2462379f35be0a3a6cb2e78506b25d1f3ee39b825e",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 9448,
      "global_seconds_exact": "1182181/3750",
      "local_seconds_exact": "57181/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F32_student.png",
      "png_sha256": "b5cb7f7e495bcbb1f8f1e45d35ac3db729410e33915421a238851a1a62de60f6",
      "rgb_pixel_sha256": "79223bdffabe5dca09a0362a7fee28cbd16c1bc7f823c262f19615a12cb81604",
      "actual_png_sha256": "b5cb7f7e495bcbb1f8f1e45d35ac3db729410e33915421a238851a1a62de60f6",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 9462,
      "global_seconds_exact": "1578577/5000",
      "local_seconds_exact": "78577/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F33_student.png",
      "png_sha256": "79d40ccb63b6a03733867ad3b47270ffc946f47d4ff8b772482e6696ec7e69aa",
      "rgb_pixel_sha256": "3d0ecced2e99e12affb9599b0bd933c6039f329841e65536c35049e5baeaaec9",
      "actual_png_sha256": "79d40ccb63b6a03733867ad3b47270ffc946f47d4ff8b772482e6696ec7e69aa",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 9476,
      "global_seconds_exact": "2371369/7500",
      "local_seconds_exact": "121369/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F34_student.png",
      "png_sha256": "1e54e810b0984f55d7b57be93f785786b6cf8985008cd1650c01585aae398541",
      "rgb_pixel_sha256": "bd99f3a7e0214b01cb2e5429516372c725fd97659054d878f66aeb60dc535c98",
      "actual_png_sha256": "1e54e810b0984f55d7b57be93f785786b6cf8985008cd1650c01585aae398541",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 9490,
      "global_seconds_exact": "949949/3000",
      "local_seconds_exact": "49949/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F35_student.png",
      "png_sha256": "dfaac6481ff20f84596aca95fc8765355885c7233aafb6f92ba43bd53d61618b",
      "rgb_pixel_sha256": "447cdde29029557c3c6457aea49c79c82ebfe01fb20edb2090863ce8e8dfa933",
      "actual_png_sha256": "dfaac6481ff20f84596aca95fc8765355885c7233aafb6f92ba43bd53d61618b",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 9505,
      "global_seconds_exact": "1902901/6000",
      "local_seconds_exact": "102901/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F36_student.png",
      "png_sha256": "1e6bc92adaf1b172ed1ad0d94f3a5102a38b8b4a2738df9371ee1b71df815963",
      "rgb_pixel_sha256": "5fde3f91eab5be14ad6f36198b44c75a95d42b0787a820b28ee26985c58b0b33",
      "actual_png_sha256": "1e6bc92adaf1b172ed1ad0d94f3a5102a38b8b4a2738df9371ee1b71df815963",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 9519,
      "global_seconds_exact": "3176173/10000",
      "local_seconds_exact": "176173/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F37_student.png",
      "png_sha256": "a6cd85adf72f6b12c8f541b31d101a380f0fcfa21f11eb807e8de0b3ec374fac",
      "rgb_pixel_sha256": "dd4c4f1b617b0d1d3e4964f0bd086fd11204fdc0a0bd9fadf5653955d7247412",
      "actual_png_sha256": "a6cd85adf72f6b12c8f541b31d101a380f0fcfa21f11eb807e8de0b3ec374fac",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 9533,
      "global_seconds_exact": "9542533/30000",
      "local_seconds_exact": "542533/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F38_student.png",
      "png_sha256": "fa98de2d0710cbba0e64eb7503bc73c787b9e3f578edb5cf216b5659d210c7d0",
      "rgb_pixel_sha256": "f64a98c5d2fcd818d0a53bf4ebd2471ebdafa986f0057ec73e50caca7773972f",
      "actual_png_sha256": "fa98de2d0710cbba0e64eb7503bc73c787b9e3f578edb5cf216b5659d210c7d0",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 9547,
      "global_seconds_exact": "9556547/30000",
      "local_seconds_exact": "556547/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F39_student.png",
      "png_sha256": "a19a6a9fbf5f6a82fcafc51b43e36f76c8080481e4c4daa208f6c3ebc6e58ce8",
      "rgb_pixel_sha256": "0aadcb689431770e9a89daa9630fd06692bd62c19fe0d53036c42abe9ca75a7d",
      "actual_png_sha256": "a19a6a9fbf5f6a82fcafc51b43e36f76c8080481e4c4daa208f6c3ebc6e58ce8",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 9562,
      "global_seconds_exact": "4785781/15000",
      "local_seconds_exact": "285781/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F40_student.png",
      "png_sha256": "c49ce196716bcfa4cb61aa93a289cd3006e1e9e3c712456fc40a6a96ef7565ae",
      "rgb_pixel_sha256": "f7f061a310de4445d1ef0f504db397d320386695c9d03e6f948a7ff81884c92d",
      "actual_png_sha256": "c49ce196716bcfa4cb61aa93a289cd3006e1e9e3c712456fc40a6a96ef7565ae",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 9576,
      "global_seconds_exact": "399399/1250",
      "local_seconds_exact": "24399/1250",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F41_student.png",
      "png_sha256": "438b2c7b5548adf2664578fbd6c31b7284620ca80e0a4135f518cf90618393db",
      "rgb_pixel_sha256": "6f58da3064684f38acb043a90a0cec804ce1730352373baa77fec112d6a58571",
      "actual_png_sha256": "438b2c7b5548adf2664578fbd6c31b7284620ca80e0a4135f518cf90618393db",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 9590,
      "global_seconds_exact": "959959/3000",
      "local_seconds_exact": "59959/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F42_student.png",
      "png_sha256": "c5f9e2d48a3b37f86bef37a04990e552d26405a0144ecdbd1f42e95635e0b34b",
      "rgb_pixel_sha256": "5f227b3036f7658edd1d0a2663e764f43fc347feeab3491c4294c2e076d50dcc",
      "actual_png_sha256": "c5f9e2d48a3b37f86bef37a04990e552d26405a0144ecdbd1f42e95635e0b34b",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 9604,
      "global_seconds_exact": "2403401/7500",
      "local_seconds_exact": "153401/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F43_student.png",
      "png_sha256": "38f0592f105250791da331904d055ddc79ad737e8a0a9abfe75c503664d97a6d",
      "rgb_pixel_sha256": "8caed5a9a389b15b8c90d309f2474043910e4a96a15096e3c51d22aff443204a",
      "actual_png_sha256": "38f0592f105250791da331904d055ddc79ad737e8a0a9abfe75c503664d97a6d",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 9619,
      "global_seconds_exact": "9628619/30000",
      "local_seconds_exact": "628619/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F44_student.png",
      "png_sha256": "3d774196f1dcff1bd795fb0c69243bfd3b71298301522dcbafdf0a8041ac169d",
      "rgb_pixel_sha256": "966056d134218cbddcf30bc17b09b27cc7d8158a99a4abd111283918bb495e29",
      "actual_png_sha256": "3d774196f1dcff1bd795fb0c69243bfd3b71298301522dcbafdf0a8041ac169d",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 9633,
      "global_seconds_exact": "3214211/10000",
      "local_seconds_exact": "214211/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F45_student.png",
      "png_sha256": "fe74f2e34d8fb103210f433d976d253d48332fc846c1a3dd61204e737bb8e71f",
      "rgb_pixel_sha256": "88d5e3c67a6ec6387aa233f98cd9f90f15d7cfd51eb8aa7580ad86c6612a877d",
      "actual_png_sha256": "fe74f2e34d8fb103210f433d976d253d48332fc846c1a3dd61204e737bb8e71f",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 9647,
      "global_seconds_exact": "9656647/30000",
      "local_seconds_exact": "656647/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F46_student.png",
      "png_sha256": "cd59d025cec205c8449d0a77d05b484173986f620f32d6e6cdb84110fbcd7c4e",
      "rgb_pixel_sha256": "ba8802d4809e13675b7d601583d0836dcf6e8103aa3ded0437741bb81d4e6f95",
      "actual_png_sha256": "cd59d025cec205c8449d0a77d05b484173986f620f32d6e6cdb84110fbcd7c4e",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 9661,
      "global_seconds_exact": "9670661/30000",
      "local_seconds_exact": "670661/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F47_student.png",
      "png_sha256": "9d85d12bcac811f9f828fd90e62fae4e8953927e80911f0f0c8f2d1e91a07d0d",
      "rgb_pixel_sha256": "ef83f66cac28bb62ff8124045c0b826f9ce3147c109496a2be46b7de07fa6300",
      "actual_png_sha256": "9d85d12bcac811f9f828fd90e62fae4e8953927e80911f0f0c8f2d1e91a07d0d",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 9676,
      "global_seconds_exact": "2421419/7500",
      "local_seconds_exact": "171419/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F48_student.png",
      "png_sha256": "c9e7cd9df183da463e61df989e9bf007214e5f161ce94bf240a6a154559aadca",
      "rgb_pixel_sha256": "6c9e5977bf732534c56c1d504a69b022e58c81d9493c5f4b28217ecbe7f590bd",
      "actual_png_sha256": "c9e7cd9df183da463e61df989e9bf007214e5f161ce94bf240a6a154559aadca",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 9690,
      "global_seconds_exact": "323323/1000",
      "local_seconds_exact": "23323/1000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F49_student.png",
      "png_sha256": "e51cd07742839d06d8491c68181161547c3f54863766f18c466299ce5a4d857f",
      "rgb_pixel_sha256": "d573c3a21f6538b06ba8fc54d30e87d041d5ddc434ffdb7de05e8558486c78e3",
      "actual_png_sha256": "e51cd07742839d06d8491c68181161547c3f54863766f18c466299ce5a4d857f",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 9704,
      "global_seconds_exact": "1214213/3750",
      "local_seconds_exact": "89213/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F50_student.png",
      "png_sha256": "47630feda66a2a7414e58ef5ea26a554f2912eb13005da10b91627df6217e981",
      "rgb_pixel_sha256": "b591980d87c24ce268110d490eace8c1d216e1ac2e96eb696e777f59a48d23e4",
      "actual_png_sha256": "47630feda66a2a7414e58ef5ea26a554f2912eb13005da10b91627df6217e981",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 9718,
      "global_seconds_exact": "4863859/15000",
      "local_seconds_exact": "363859/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F51_student.png",
      "png_sha256": "ed59b14ca3d04f2dafbd5ba7ef777f797f76b870bcc962aefc118678b1bcbc89",
      "rgb_pixel_sha256": "a3e4d49954decb8b7e3843a36e4c0a2d2bb4fbbb300cf299fffe9fe356687fc0",
      "actual_png_sha256": "ed59b14ca3d04f2dafbd5ba7ef777f797f76b870bcc962aefc118678b1bcbc89",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 9733,
      "global_seconds_exact": "9742733/30000",
      "local_seconds_exact": "742733/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F52_student.png",
      "png_sha256": "06db521ec7771fc407c3d27568bfe2c07e5ca9c8e605d9168cb1e7f3dfcd0980",
      "rgb_pixel_sha256": "7efd5529eff0442c284cdc6ee46572f0fa59f5215e21d748d4f97fcacbe19db5",
      "actual_png_sha256": "06db521ec7771fc407c3d27568bfe2c07e5ca9c8e605d9168cb1e7f3dfcd0980",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 9747,
      "global_seconds_exact": "3252249/10000",
      "local_seconds_exact": "252249/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F53_student.png",
      "png_sha256": "39c22870bd03f6375f103fecac43dc2210f2cef8a20ad714e653b33bdfd844db",
      "rgb_pixel_sha256": "68ef5fc4c2b53c07917501dac26c37b9bdda403dac1c57ea24d70fa3d8aa5550",
      "actual_png_sha256": "39c22870bd03f6375f103fecac43dc2210f2cef8a20ad714e653b33bdfd844db",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 9761,
      "global_seconds_exact": "9770761/30000",
      "local_seconds_exact": "770761/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F54_student.png",
      "png_sha256": "21d5ca73bd5a32f5d3a5d284a4da467b157da109e7740fd47d6f059fb19441d4",
      "rgb_pixel_sha256": "d916419392fed1f4d31ee86e4dfda37dd9e7fb9396d612c3c2639bd4ff29f373",
      "actual_png_sha256": "21d5ca73bd5a32f5d3a5d284a4da467b157da109e7740fd47d6f059fb19441d4",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 9775,
      "global_seconds_exact": "391391/1200",
      "local_seconds_exact": "31391/1200",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F55_student.png",
      "png_sha256": "7179d0cca2b1011152c1927d359c48b99c6d70df19092562241ac953d4df4190",
      "rgb_pixel_sha256": "e49afaf10d1c88733e3c070eea2a3204bf8552834dd197ae13ab818bbaa633d3",
      "actual_png_sha256": "7179d0cca2b1011152c1927d359c48b99c6d70df19092562241ac953d4df4190",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 9790,
      "global_seconds_exact": "979979/3000",
      "local_seconds_exact": "79979/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F56_student.png",
      "png_sha256": "7e5196ee177b185a7c80584a004851a2fe87aa9f0a6110ea7ae0a1504741fa1e",
      "rgb_pixel_sha256": "2e9a04d663da8c90a27c7ff8959d3da0b32b345ab0c42b63d125c7a3c18af401",
      "actual_png_sha256": "7e5196ee177b185a7c80584a004851a2fe87aa9f0a6110ea7ae0a1504741fa1e",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 9804,
      "global_seconds_exact": "817817/2500",
      "local_seconds_exact": "67817/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F57_student.png",
      "png_sha256": "e3af4b8c5b4cd0edff69e97913fd668dfe6cc32b227716c23538d4fe4207e8a2",
      "rgb_pixel_sha256": "658f923470f2bf18c01bbe7f425669197d5f44f16a75809a316fe88447d1fe73",
      "actual_png_sha256": "e3af4b8c5b4cd0edff69e97913fd668dfe6cc32b227716c23538d4fe4207e8a2",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 9818,
      "global_seconds_exact": "4913909/15000",
      "local_seconds_exact": "413909/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F58_student.png",
      "png_sha256": "702722b59a133be15d8b2a1b4bdae64e6539b6f7c4ece347bd3b3127557f8c05",
      "rgb_pixel_sha256": "36d89d2c3a1bae0f74540afc055fc33e8ebd18192e9468e413563c54d024429b",
      "actual_png_sha256": "702722b59a133be15d8b2a1b4bdae64e6539b6f7c4ece347bd3b3127557f8c05",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 9832,
      "global_seconds_exact": "1230229/3750",
      "local_seconds_exact": "105229/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F59_student.png",
      "png_sha256": "c49358f750e249de87655c920cffaa65a509cffe15066a5900a3c56253506020",
      "rgb_pixel_sha256": "c9cf78f447d43efdf690a1c747fc6e947b5dfce0e8cb2e96076a6da2c6e37df4",
      "actual_png_sha256": "c49358f750e249de87655c920cffaa65a509cffe15066a5900a3c56253506020",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 9847,
      "global_seconds_exact": "9856847/30000",
      "local_seconds_exact": "856847/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F60_student.png",
      "png_sha256": "a33c4b2b95f11d5b6658b87d928b3c69807c1f6c808942eefad50be724454ea6",
      "rgb_pixel_sha256": "68c8e2f6b134d6fcd4222a3146e3e9c05aa5db20e4664fa6ef557ab29a7e732e",
      "actual_png_sha256": "a33c4b2b95f11d5b6658b87d928b3c69807c1f6c808942eefad50be724454ea6",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 9861,
      "global_seconds_exact": "3290287/10000",
      "local_seconds_exact": "290287/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F61_student.png",
      "png_sha256": "8cadbf6a1a152623315ff505d8164ce2c26ddaac33f6d0cfd195dfcd5b8f267d",
      "rgb_pixel_sha256": "18e77029ab0dfb1db0d26ab67e119138bf43ee4f16c59273334f8b9b7a099e33",
      "actual_png_sha256": "8cadbf6a1a152623315ff505d8164ce2c26ddaac33f6d0cfd195dfcd5b8f267d",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 9875,
      "global_seconds_exact": "79079/240",
      "local_seconds_exact": "7079/240",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F62_student.png",
      "png_sha256": "a6cf1628912d5ae00bfbeac2332ac705d7d1ad48512c3d21cef62cae99c28b62",
      "rgb_pixel_sha256": "3a81674e4aff2498b61f6052bb700e198522ab01f24c4698a9a2e79e4e6e83fb",
      "actual_png_sha256": "a6cf1628912d5ae00bfbeac2332ac705d7d1ad48512c3d21cef62cae99c28b62",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 9890,
      "global_seconds_exact": "989989/3000",
      "local_seconds_exact": "89989/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\02_AwmHb44_ouw_W10\\student_views\\F63_student.png",
      "png_sha256": "f09645a799b0e2387eb65a4d534acff39b6642f09d6449932292dddb3c83f13e",
      "rgb_pixel_sha256": "a54e042e5792dc6b9703d6101c184b04dbbbc85a325961e6a20f80eea8dddf23",
      "actual_png_sha256": "f09645a799b0e2387eb65a4d534acff39b6642f09d6449932292dddb3c83f13e",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    }
  ]
}



## 完整新增公开证据：02_AwmHb44_ouw_W10.independent_student_view_review_v1.md
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\02_AwmHb44_ouw_W10.independent_student_view_review_v1.md
字节：1281；SHA256：19782d0b5307d0a21096d9ce8dcea5d7d24e6a95dc36ff0d56e53d47afaf6db5

# AwmHb44_ouw:SLOT6:10 有效视图独立续审

已通过view_image读完64张实际本地CPU tensor重构PNG（8批），全部SHA与receipt相符，source ordinal及exact PTS与初稿逐项一致。初稿引用SHA：a8b6e30dcc4fdd79fe4ef53bc6b2f7605ae06616d62aa9c7faaad9c56e46904d。

544x352有效显示仍见F00-F04手指接触轮圈内侧点，但点的功能或完成操作不可判。F05-F23轮胎/喷瓶/扳手布局可辨。F24-F63人物嘴型与背景可见，本轮未提供音频证据，讲述意义未知不变。原K/NO/U不变。

K/NO/U无变更；原具体UNKNOWN保留。未决问题影响完整窗口目标：连续人物讲述意义未知，且F00-F04接触点的机械功能/结果未知；不确认台词、工具使用或修复成功。影响完整窗口目标。 对应帧：F24, F25, F26, F27, F28, F29, F30, F31, F32, F33, F34, F35, F36, F37, F38, F39, F40, F41, F42, F43, F44, F45, F46, F47, F48, F49, F50, F51, F52, F53, F54, F55, F56, F57, F58, F59, F60, F61, F62, F63。

student_processor_visibility_verified=true（仅本地CPU实际显示视图）；Linux execution=false；training_admitted=false；full_native_frames_observed=false；full_window_target_admitted=false。仍未接收或读取教师内容；可见性不是完整训练资格。



## 完整新增公开证据：proposal.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\03_AwmHb44_ouw_W11\teacher_attempt01_http1\proposal.json
字节：22373；SHA256：bd8bc71d4e2d53d3f1b010c5891e073fd251624333c467ff0a11518c10690ed2

{
  "window_id": "AwmHb44_ouw:SLOT6:11",
  "source_sha256": "82ecca1de0363253060bb3c19e2f5dbd4080bfc0cd790db23c3e73ffd76a602f",
  "clip_sha256": "6f9b6ad70e644141b6f3995be70ed6eceb30219afc28b9761cef0151015d3fe4",
  "model": "Gemini 3.8 Flash (High)",
  "native_video_actual_scope": "clip.mp4 通过 view_file 工具进行了一次观察，工具内部实施了每秒1帧、00:00至00:23共24张画面缩略采样（覆盖00:00-00:23秒域），该内部采样机制不透明且非逐帧完全读取；全窗口原生帧通过64张密集抽样原生PNG（F00-F63，覆盖0.0297s至23.5532s）及8张学生有效重构视图完成真实可见性检验与客观事实观察。",
  "full_native_frames_observed": false,
  "frame_observations": [
    {
      "frame_id": "F00",
      "source_ordinal": 9891,
      "local_seconds_exact": 0.0297,
      "observed": true,
      "visible_fact": "中年男性面向镜头特写，双唇微闭，目光正视前方偏右，背景为户外木栅栏、白色平房及停放的深色车辆。"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 9902,
      "local_seconds_exact": 0.39673333333333335,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微张开始说话，神情平稳，背景无变动。"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 9913,
      "local_seconds_exact": 0.7637666666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇张开微露齿，处于口头讲话状态。"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 9924,
      "local_seconds_exact": 1.1308,
      "observed": true,
      "visible_fact": "中年男性特写，嘴型张开幅度较明显，面部肌肉伴随发音微动。"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 9935,
      "local_seconds_exact": 1.4978333333333334,
      "observed": true,
      "visible_fact": "中年男性特写，下唇微闭，嘴型收敛发音。"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 9946,
      "local_seconds_exact": 1.8648666666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微合接近闭合，目光注视前方。"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 9958,
      "local_seconds_exact": 2.2652666666666666,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇再度微张，面部保持正对镜头构图。"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 9969,
      "local_seconds_exact": 2.6323,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部开合，持续口语发音动作。"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9980,
      "local_seconds_exact": 2.9993333333333334,
      "observed": true,
      "visible_fact": "中年男性特写，嘴微张露门齿，面部肌肉微动，背景无变化。"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 9991,
      "local_seconds_exact": 3.3663666666666667,
      "observed": true,
      "visible_fact": "中年男性特写，下颌微抬，嘴部微开，继续讲话。"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 10002,
      "local_seconds_exact": 3.7334,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴张开，处于发音进行中。"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 10014,
      "local_seconds_exact": 4.1338,
      "observed": true,
      "visible_fact": "中年男性特写，嘴型收窄微开，目光凝视镜头。"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 10025,
      "local_seconds_exact": 4.500833333333333,
      "observed": true,
      "visible_fact": "中年男性特写，双唇接近闭合，表情平静叙述。"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 10036,
      "local_seconds_exact": 4.8678666666666665,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴微张，头颈部位置保持基本稳定。"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 10047,
      "local_seconds_exact": 5.2349,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微闭，短暂停顿口型。"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 10058,
      "local_seconds_exact": 5.601933333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部微开，继续口头叙述。"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 10070,
      "local_seconds_exact": 6.0023333333333335,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴张开，露上下齿口型。"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 10081,
      "local_seconds_exact": 6.369366666666667,
      "observed": true,
      "visible_fact": "中年男性特写，下唇微收，口型变化发音。"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 10092,
      "local_seconds_exact": 6.7364,
      "observed": true,
      "visible_fact": "中年男性特写，双唇闭合收拢，保持正面特写构图。"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 10103,
      "local_seconds_exact": 7.103433333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴型微张，口部动作连贯。"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 10114,
      "local_seconds_exact": 7.470466666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微张呈椭圆口型发音。"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 10126,
      "local_seconds_exact": 7.870866666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部微合，眼神专注直视前方。"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 10137,
      "local_seconds_exact": 8.2379,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴再度张开，处于连贯发音过程。"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 10148,
      "local_seconds_exact": 8.604933333333333,
      "observed": true,
      "visible_fact": "中年男性特写，口型微变，持续口述无其他动作。"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 10159,
      "local_seconds_exact": 8.971966666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微抿闭合，背景木栅栏与房屋保持静止。"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 10170,
      "local_seconds_exact": 9.339,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇张开微露齿，口述持续。"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 10181,
      "local_seconds_exact": 9.706033333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴型微收，目光注视镜头。"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 10193,
      "local_seconds_exact": 10.106433333333333,
      "observed": true,
      "visible_fact": "中年男性特写，下颌轻动，嘴部开合说话。"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 10204,
      "local_seconds_exact": 10.473466666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴微开，表情自然陈述。"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 10215,
      "local_seconds_exact": 10.8405,
      "observed": true,
      "visible_fact": "中年男性特写，双唇微闭，短暂停顿口型。"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 10226,
      "local_seconds_exact": 11.207533333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微张，重新开始发音。"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 10237,
      "local_seconds_exact": 11.574566666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微合，姿态与光线恒定。"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 10249,
      "local_seconds_exact": 11.974966666666667,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部张开说话，双眼注视前方。"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 10260,
      "local_seconds_exact": 12.342,
      "observed": true,
      "visible_fact": "中年男性特写，口型稍敛，面部肌肉微动。"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 10271,
      "local_seconds_exact": 12.709033333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴张开微露齿，口语表述中。"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 10282,
      "local_seconds_exact": 13.076066666666667,
      "observed": true,
      "visible_fact": "中年男性特写，双唇收紧微开，保持同一说话机位。"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 10293,
      "local_seconds_exact": 13.4431,
      "observed": true,
      "visible_fact": "中年男性特写，下颌略垂，嘴型微开露缝。"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 10305,
      "local_seconds_exact": 13.8435,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微闭，面容保持同一取景。"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 10316,
      "local_seconds_exact": 14.210533333333334,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部微张露齿，持续口述。"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 10327,
      "local_seconds_exact": 14.577566666666666,
      "observed": true,
      "visible_fact": "中年男性特写，嘴形微合，目光未移开镜头。"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 10338,
      "local_seconds_exact": 14.9446,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴张开，呈发音动作。"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 10349,
      "local_seconds_exact": 15.311633333333333,
      "observed": true,
      "visible_fact": "中年男性特写，双唇微张微合，动作连续。"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 10361,
      "local_seconds_exact": 15.712033333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴张开说话，背景环境静止。"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 10372,
      "local_seconds_exact": 16.079066666666668,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微收，口语讲述中。"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 10383,
      "local_seconds_exact": 16.4461,
      "observed": true,
      "visible_fact": "中年男性特写，双唇闭合微留缝隙，头颈无大位移。"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 10394,
      "local_seconds_exact": 16.813133333333335,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴微张，神态平静。"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 10405,
      "local_seconds_exact": 17.180166666666667,
      "observed": true,
      "visible_fact": "中年男性特写，下颌微动，嘴型开合发音。"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 10416,
      "local_seconds_exact": 17.5472,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微敛闭合，陈述持续。"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 10428,
      "local_seconds_exact": 17.9476,
      "observed": true,
      "visible_fact": "中年男性特写，嘴微开露门齿，面部肌肉微动。"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 10439,
      "local_seconds_exact": 18.314633333333334,
      "observed": true,
      "visible_fact": "中年男性特写，双唇微张，正面特写讲话。"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 10450,
      "local_seconds_exact": 18.681666666666665,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部张开说话，表情自然连贯。"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 10461,
      "local_seconds_exact": 19.0487,
      "observed": true,
      "visible_fact": "中年男性特写，口型微敛，目光凝视前方镜头。"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 10472,
      "local_seconds_exact": 19.415733333333334,
      "observed": true,
      "visible_fact": "中年男性特写，双唇微闭，短暂停顿口型。"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 10484,
      "local_seconds_exact": 19.816133333333335,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇张开发音，双眼直视镜头。"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 10495,
      "local_seconds_exact": 20.183166666666666,
      "observed": true,
      "visible_fact": "中年男性特写，口型收拢，继续进行讲话。"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 10506,
      "local_seconds_exact": 20.5502,
      "observed": true,
      "visible_fact": "中年男性特写，下唇微启，面部表情基本恒定。"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 10517,
      "local_seconds_exact": 20.917233333333335,
      "observed": true,
      "visible_fact": "中年男性特写，嘴微开，专注面对镜头陈述。"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 10528,
      "local_seconds_exact": 21.284266666666668,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微合，姿态平稳。"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 10540,
      "local_seconds_exact": 21.684666666666665,
      "observed": true,
      "visible_fact": "中年男性特写，嘴巴微张说话，背景无任何异常异动。"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 10551,
      "local_seconds_exact": 22.0517,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部微合，持续口语表述。"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 10562,
      "local_seconds_exact": 22.418733333333333,
      "observed": true,
      "visible_fact": "中年男性特写，嘴型张开发音，眼神专注。"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 10573,
      "local_seconds_exact": 22.785766666666666,
      "observed": true,
      "visible_fact": "中年男性特写，嘴唇微敛收缩口型。"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 10584,
      "local_seconds_exact": 23.1528,
      "observed": true,
      "visible_fact": "中年男性特写，双唇微张，仍在面对镜头叙述。"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 10596,
      "local_seconds_exact": 23.5532,
      "observed": true,
      "visible_fact": "中年男性特写，嘴部微开保持叙述状态，窗口观测终末帧。"
    }
  ],
  "effective_view_observations": [
    {
      "frame_id": "F00",
      "source_ordinal": 9891,
      "local_seconds_exact": 0.0297,
      "observed": true,
      "visible_fact": "学生视图显示该中年男子面部正对镜头的近景特写，五官、小胡子与背景木栅栏轮廓清晰可见，双唇微闭。",
      "student_visibility_assessment": "主体人物面部轮廓、发型与八字胡清晰可辨，背景房屋及深色车辆边界分明；虽因降采样与反归一化重构在胡须微观纹理上稍有平滑，但整体人物讲话姿态与视觉主体完全可识别。"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9980,
      "local_seconds_exact": 2.9993333333333334,
      "observed": true,
      "visible_fact": "学生视图显示男子面部特写，嘴唇微启微露齿，保持同一户外正面构图。",
      "student_visibility_assessment": "口部开合发音状态在学生分辨率下清晰可识别，背景栅栏与车辆无形变失真，足以支撑视觉事实判断。"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 10070,
      "local_seconds_exact": 6.0023333333333335,
      "observed": true,
      "visible_fact": "学生视图显示男子嘴巴张开讲话，目光直视镜头，五官表情完整。",
      "student_visibility_assessment": "嘴型张开及眼部神态均清晰呈现，无伪影断层，与原生画面表现完全一致。"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 10159,
      "local_seconds_exact": 8.971966666666667,
      "observed": true,
      "visible_fact": "学生视图显示男子双唇微合微抿，神色凝重直视镜头。",
      "student_visibility_assessment": "嘴唇闭合姿态及面部轮廓可辨，反归一化像素微小量化误差未影响说话动作与表情状态的判读。"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 10249,
      "local_seconds_exact": 11.974966666666667,
      "observed": true,
      "visible_fact": "学生视图显示男子嘴型微张说话，面部特征与背景构图恒定保持。",
      "student_visibility_assessment": "头部位置与说话状态连续，学生特征维度完整保留了 talking-head 视觉本质。"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 10338,
      "local_seconds_exact": 14.9446,
      "observed": true,
      "visible_fact": "学生视图显示男子嘴巴张开，呈发音动作，正面特写。",
      "student_visibility_assessment": "下颌下移及双唇开张动作在学生视图中明显可见，无信息阻断。"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 10428,
      "local_seconds_exact": 17.9476,
      "observed": true,
      "visible_fact": "学生视图显示男子嘴微张露门齿，持续讲话表情。",
      "student_visibility_assessment": "口型开合细节在544x352分辨率下保持足够辨识度，人物未离开镜头中心区域。"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 10517,
      "local_seconds_exact": 20.917233333333335,
      "observed": true,
      "visible_fact": "学生视图显示男子微开双唇持续陈述，背景静止。",
      "student_visibility_assessment": "末段人物特写形态完好，画面噪点与微量化损失不影响整体事件性质识别。"
    }
  ],
  "events": [],
  "window_coverage": [
    {
      "start": 0.0,
      "end": 23.58656666666667,
      "label": "NO",
      "visible_basis": "在窗口0.0s至23.5866s全程（实际观测覆盖F00至F63），画面自始至终为单机位固定中近景特写，由同一名中年男性人物面向镜头进行户外口头叙述（talking-head monologue）。全窗口内无任何道具或物体展示、无肢体互动操作、无关键动作起伏转折、无场景切换，亦无任何动作结果展示，视觉信息密度恒定且缺乏编辑高光价值，判定为全域非高光（NO）。",
      "evidence_frame_ids": [
        "F00", "F01", "F02", "F03", "F04", "F05", "F06", "F07",
        "F08", "F09", "F10", "F11", "F12", "F13", "F14", "F15",
        "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23",
        "F24", "F25", "F26", "F27", "F28", "F29", "F30", "F31",
        "F32", "F33", "F34", "F35", "F36", "F37", "F38", "F39",
        "F40", "F41", "F42", "F43", "F44", "F45", "F46", "F47",
        "F48", "F49", "F50", "F51", "F52", "F53", "F54", "F55",
        "F56", "F57", "F58", "F59", "F60", "F61", "F62", "F63"
      ]
    }
  ],
  "consequential_unknowns": [],
  "explicit_no_highlight": [
    {
      "segment_id": "no_highlight_full_window",
      "proposed_local_seconds": [
        0.0,
        23.58656666666667
      ],
      "reason": "单人户外无声口述特写，无关键视觉动作、互动、物体展示或视觉高光结果",
      "observed_basis": "从F00(local 0.0297s)持续至F63(local 23.5532s)，画面为单一镜头中年男子面部讲话特写，背景栅栏与车辆静止，全程无动作事件转折，不符合query-free视觉高光标准",
      "evidence_frame_ids": [
        "F00", "F01", "F02", "F03", "F04", "F05", "F06", "F07",
        "F08", "F09", "F10", "F11", "F12", "F13", "F14", "F15",
        "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23",
        "F24", "F25", "F26", "F27", "F28", "F29", "F30", "F31",
        "F32", "F33", "F34", "F35", "F36", "F37", "F38", "F39",
        "F40", "F41", "F42", "F43", "F44", "F45", "F46", "F47",
        "F48", "F49", "F50", "F51", "F52", "F53", "F54", "F55",
        "F56", "F57", "F58", "F59", "F60", "F61", "F62", "F63"
      ],
      "boundary_inside_frame_ids": [
        "F00",
        "F63"
      ],
      "boundary_outside_frame_ids": [],
      "start_uncertainty_range": [
        0.0,
        0.0297
      ],
      "end_uncertainty_range": [
        23.5532,
        23.58656666666667
      ]
    }
  ],
  "student_visibility_limitations": [
    "学生有效视图分辨率为544x352并经由patch反排与归一化逆转换重构，相比原生540x360 RGB PNG在胡须细微毛发轮廓、眼周极微表情纹理及远景树枝细节上存在微弱量化模糊与平滑；但人物面部主体、五官形态、口型开合状态及静态背景结构依然清晰可辨，其感知能力足以确认该片段为单人说话特写，未引入导致高光决策改变的语义降级或信息断层。"
  ],
  "limitations": [
    "抽样观测采用稀疏帧采样（共64帧，约2.71 fps，平均采样间隔0.36~0.40秒），帧间理论上存在不可见毫秒级微动作残留风险，属于标准稀疏采样已知局限；",
    "剪辑视频 clip.mp4 无伴音轨道（no audio），且标注规约严格禁止推测音频讲述动机与语义，本提案基于纯视觉客观事实进行判定；",
    "clip.mp4 工具单次观察存在非透明的1fps内部采样，不能替代对全部底层原生帧的完整时空感知；",
    "本提案仅代表有限观察条件下的窗口完整银标建议（Silver Proposal），非金标（Gold Label），绝不授予模型训练资格（training_admitted: false）。"
  ],
  "training_admitted": false
}


## 完整新增公开证据：audit.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\03_AwmHb44_ouw_W11\teacher_attempt01_http1\audit.json
字节：13428；SHA256：1d23c18a43c750dbda41cba08f83db477ea3cb8ec31a473be9dde23244a8ea2e

{
  "status": "OBSERVATION_AUDIT_ONLY_NOT_SILVER_ADMISSION",
  "window_id": "AwmHb44_ouw:SLOT6:11",
  "actual_model": "gemini-3.8-flash-high",
  "actual_result_status": "SUCCESS",
  "actual_result_error": null,
  "actual_result_usage": {
    "input_tokens": 590252,
    "output_tokens": 41625,
    "thinking_tokens": 24514,
    "cache_read_tokens": 2109605,
    "total_tokens": 631877
  },
  "original_pngs_delivered": 64,
  "original_pngs_expected": 64,
  "missing_original": [],
  "effective_pngs_delivered": 8,
  "effective_pngs_expected": 8,
  "native_video_delivered": true,
  "actual_completed_tool_count": 81,
  "read_counts": {
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\manifest.json": 3,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\receipt.json": 3,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\clip.mp4": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F00_O009891.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F01_O009902.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F02_O009913.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F03_O009924.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F04_O009935.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F05_O009946.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F06_O009958.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F07_O009969.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F08_O009980.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F09_O009991.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F10_O010002.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F11_O010014.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F12_O010025.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F13_O010036.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F14_O010047.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F15_O010058.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F16_O010070.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F17_O010081.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F18_O010092.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F19_O010103.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F20_O010114.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F21_O010126.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F22_O010137.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F23_O010148.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F24_O010159.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F25_O010170.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F26_O010181.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F27_O010193.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F28_O010204.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F29_O010215.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F30_O010226.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F31_O010237.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F32_O010249.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F33_O010260.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F34_O010271.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F35_O010282.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F36_O010293.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F37_O010305.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F38_O010316.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F39_O010327.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F40_O010338.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F41_O010349.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F42_O010361.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F43_O010372.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F44_O010383.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F45_O010394.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F46_O010405.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F47_O010416.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F48_O010428.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F49_O010439.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F50_O010450.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F51_O010461.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F52_O010472.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F53_O010484.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F54_O010495.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F55_O010506.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F56_O010517.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F57_O010528.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F58_O010540.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F59_O010551.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F60_O010562.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F61_O010573.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F62_O010584.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F63_O010596.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F00_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F08_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F16_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F24_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F32_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F40_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F48_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F56_student.png": 1,
    "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\teacher_attempt01_http1\\proposal.json": 1
  },
  "tool_issues": [
    {
      "tool": "view_file",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\teacher_attempt01_http1\\proposal.json",
      "reason": "OUTSIDE_WHITELIST"
    }
  ],
  "proposal_geometry_identity_issues": [
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS",
    "FRAME_PTS"
  ],
  "proposal_events": 0,
  "consequential_unknown_coverage": false,
  "proposal_sha256": "bd8bc71d4e2d53d3f1b010c5891e073fd251624333c467ff0a11518c10690ed2",
  "stream_sha256": "c0e0cd6e0931e0f97fa600ed9491e095a67f39e5a7453f426c2be4623e324157",
  "request_sha256": "346ca2c29c82153c0beb27cffeee2fc48684de7bd7427720d4aa834887db770e",
  "all_floor64_delivered_not_attention_or_full_native_proof": true,
  "training_admitted": false,
  "new_optimizer_updates": 0
}

## 完整新增公开证据：terminal.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\03_AwmHb44_ouw_W11\teacher_attempt01_http1\terminal.json
字节：266；SHA256：e1fb8a747d7331571ec13d8658e3f22799691b7a32ae4bb2e87e8c465af96f9a

{
  "started_utc": "2026-10-10T06:17:26.534504+00:00",
  "finished_utc": "2026-10-10T06:25:00.889090+00:00",
  "exit_code": 0,
  "elapsed_seconds": 454.34400000000005,
  "proposal_exists": true,
  "exit_zero_not_success": true,
  "new_optimizer_updates": 0
}

## 完整新增公开证据：main_metadata_correction_v1.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\observations\03_AwmHb44_ouw_W11\teacher_attempt01_http1\main_metadata_correction_v1.json
字节：7850；SHA256：6b7872ef0f6efe393d552a8fdd1b8e994cfd051a075cc6e4fc24fdc031c86fe5

{
  "status": "MAIN_METADATA_CORRECTION_SIDECAR_NOT_SILVER_ADMISSION",
  "source_proposal_sha256": "bd8bc71d4e2d53d3f1b010c5891e073fd251624333c467ff0a11518c10690ed2",
  "raw_unchanged": true,
  "frame_ordinals_match": true,
  "mismatches": [
    {
      "frame_id": "F01",
      "teacher_time": 0.3967333333333333,
      "manifest_exact": "5951/15000",
      "absolute_error_exact": "1/30000000000000000"
    },
    {
      "frame_id": "F02",
      "teacher_time": 0.7637666666666667,
      "manifest_exact": "22913/30000",
      "absolute_error_exact": "1/30000000000000000"
    },
    {
      "frame_id": "F04",
      "teacher_time": 1.4978333333333333,
      "manifest_exact": "8987/6000",
      "absolute_error_exact": "1/30000000000000000"
    },
    {
      "frame_id": "F05",
      "teacher_time": 1.8648666666666667,
      "manifest_exact": "27973/15000",
      "absolute_error_exact": "1/30000000000000000"
    },
    {
      "frame_id": "F06",
      "teacher_time": 2.2652666666666668,
      "manifest_exact": "33979/15000",
      "absolute_error_exact": "1/7500000000000000"
    },
    {
      "frame_id": "F08",
      "teacher_time": 2.9993333333333334,
      "manifest_exact": "4499/1500",
      "absolute_error_exact": "1/15000000000000000"
    },
    {
      "frame_id": "F09",
      "teacher_time": 3.3663666666666665,
      "manifest_exact": "100991/30000",
      "absolute_error_exact": "1/6000000000000000"
    },
    {
      "frame_id": "F12",
      "teacher_time": 4.500833333333333,
      "manifest_exact": "5401/1200",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F13",
      "teacher_time": 4.867866666666666,
      "manifest_exact": "36509/7500",
      "absolute_error_exact": "1/1500000000000000"
    },
    {
      "frame_id": "F15",
      "teacher_time": 5.601933333333333,
      "manifest_exact": "84029/15000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F16",
      "teacher_time": 6.0023333333333335,
      "manifest_exact": "18007/3000",
      "absolute_error_exact": "1/6000000000000000"
    },
    {
      "frame_id": "F17",
      "teacher_time": 6.369366666666667,
      "manifest_exact": "191081/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F19",
      "teacher_time": 7.103433333333333,
      "manifest_exact": "213103/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F20",
      "teacher_time": 7.470466666666667,
      "manifest_exact": "112057/15000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F21",
      "teacher_time": 7.870866666666667,
      "manifest_exact": "118063/15000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F23",
      "teacher_time": 8.604933333333333,
      "manifest_exact": "64537/7500",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F24",
      "teacher_time": 8.971966666666667,
      "manifest_exact": "269159/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F26",
      "teacher_time": 9.706033333333332,
      "manifest_exact": "291181/30000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F27",
      "teacher_time": 10.106433333333333,
      "manifest_exact": "303193/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F28",
      "teacher_time": 10.473466666666667,
      "manifest_exact": "78551/7500",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F30",
      "teacher_time": 11.207533333333332,
      "manifest_exact": "168113/15000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F31",
      "teacher_time": 11.574566666666668,
      "manifest_exact": "347237/30000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F32",
      "teacher_time": 11.974966666666667,
      "manifest_exact": "359249/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F34",
      "teacher_time": 12.709033333333332,
      "manifest_exact": "381271/30000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F35",
      "teacher_time": 13.076066666666668,
      "manifest_exact": "196141/15000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F38",
      "teacher_time": 14.210533333333334,
      "manifest_exact": "106579/7500",
      "absolute_error_exact": "1/1500000000000000"
    },
    {
      "frame_id": "F39",
      "teacher_time": 14.577566666666666,
      "manifest_exact": "437327/30000",
      "absolute_error_exact": "1/1500000000000000"
    },
    {
      "frame_id": "F41",
      "teacher_time": 15.311633333333333,
      "manifest_exact": "459349/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F42",
      "teacher_time": 15.712033333333332,
      "manifest_exact": "471361/30000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F43",
      "teacher_time": 16.07906666666667,
      "manifest_exact": "120593/7500",
      "absolute_error_exact": "1/300000000000000"
    },
    {
      "frame_id": "F45",
      "teacher_time": 16.813133333333337,
      "manifest_exact": "252197/15000",
      "absolute_error_exact": "11/3000000000000000"
    },
    {
      "frame_id": "F46",
      "teacher_time": 17.18016666666667,
      "manifest_exact": "103081/6000",
      "absolute_error_exact": "1/300000000000000"
    },
    {
      "frame_id": "F49",
      "teacher_time": 18.314633333333333,
      "manifest_exact": "549439/30000",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F50",
      "teacher_time": 18.681666666666665,
      "manifest_exact": "11209/600",
      "absolute_error_exact": "1/600000000000000"
    },
    {
      "frame_id": "F52",
      "teacher_time": 19.415733333333336,
      "manifest_exact": "72809/3750",
      "absolute_error_exact": "1/375000000000000"
    },
    {
      "frame_id": "F53",
      "teacher_time": 19.816133333333337,
      "manifest_exact": "148621/7500",
      "absolute_error_exact": "11/3000000000000000"
    },
    {
      "frame_id": "F54",
      "teacher_time": 20.183166666666665,
      "manifest_exact": "121099/6000",
      "absolute_error_exact": "1/600000000000000"
    },
    {
      "frame_id": "F56",
      "teacher_time": 20.917233333333336,
      "manifest_exact": "627517/30000",
      "absolute_error_exact": "1/375000000000000"
    },
    {
      "frame_id": "F57",
      "teacher_time": 21.284266666666667,
      "manifest_exact": "39908/1875",
      "absolute_error_exact": "1/3000000000000000"
    },
    {
      "frame_id": "F58",
      "teacher_time": 21.684666666666665,
      "manifest_exact": "32527/1500",
      "absolute_error_exact": "1/600000000000000"
    },
    {
      "frame_id": "F60",
      "teacher_time": 22.418733333333332,
      "manifest_exact": "336281/15000",
      "absolute_error_exact": "1/750000000000000"
    },
    {
      "frame_id": "F61",
      "teacher_time": 22.785766666666667,
      "manifest_exact": "683573/30000",
      "absolute_error_exact": "1/3000000000000000"
    }
  ],
  "max_absolute_error_seconds_exact": "11/3000000000000000",
  "semantic_labels_modified": false,
  "self_proposal_read_outside_requested_whitelist_not_retroactively_authorized": true,
  "training_admitted": false
}

## 完整新增公开证据：03_AwmHb44_ouw_W11.independent_initial_blind_v1.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\03_AwmHb44_ouw_W11.independent_initial_blind_v1.json
字节：62049；SHA256：4f4f9a9b38340f778ac6347da26af2e4a3dda6818c373b9840824f118f039afa

{
  "schema": "independent_initial_blind_review_v1",
  "review_utc": "2026-10-10 05:47:39 UTC",
  "reviewer": "独立执行Agent",
  "review_kind": "INITIAL_SAMPLED_NATIVE_PNG_BLIND_REVIEW",
  "window_id": "AwmHb44_ouw:SLOT6:11",
  "source_id": "AwmHb44_ouw",
  "source_identity_manifest_declared": {
    "source_sha256": "82ecca1de0363253060bb3c19e2f5dbd4080bfc0cd790db23c3e73ffd76a602f",
    "source_total_frames": 10597,
    "source_file_independently_read_or_hashed": false
  },
  "manifest": {
    "path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/observations/03_AwmHb44_ouw_W11/manifest.json",
    "sha256_as_initial_read": "a912670f4927a6500558243a0be966d2eb931e87bfda76f928ce27eae7036f91",
    "plan_sha256": "09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22",
    "domain_global_seconds_exact": [
      "330",
      "35358656666666667/100000000000000"
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
    "sample_max_gap_seconds_approx": 0.4004000000000474,
    "sampling_residual_risk": "仅观察floor64样本，短瞬时动作、遮挡、镜头切点与非采样变化仍可能漏掉。稳定同镜头重复间隙未机械标UNKNOWN；已识别能改变标签的切点、失焦与讲述意义列具体U。边界须后续更密帧证据核验。"
  },
  "segments": [
    {
      "segment_id": "S01",
      "label": "U",
      "global_seconds_exact": [
        "330",
        "35358656666666667/100000000000000"
      ],
      "title": "全窗连续人物近景的讲述意义",
      "visual_reason_or_unknown": "所有样本都是同一户外人物面部近景，嘴型与眼睑变化；没有音频/转录，是否包含必须保留的解释/结论无法判断。未见独立手势、工具操作、新物体或显著构图变化；不据此默认NO。",
      "evidence_frames": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04",
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
        "F23",
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
  "keep_events": [],
  "explicit_no_intervals": [],
  "unknown_intervals": [
    {
      "segment_id": "S01",
      "label": "U",
      "global_seconds_exact": [
        "330",
        "35358656666666667/100000000000000"
      ],
      "title": "全窗连续人物近景的讲述意义",
      "visual_reason_or_unknown": "所有样本都是同一户外人物面部近景，嘴型与眼睑变化；没有音频/转录，是否包含必须保留的解释/结论无法判断。未见独立手势、工具操作、新物体或显著构图变化；不据此默认NO。",
      "evidence_frames": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04",
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
        "F23",
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
  "no_interval_note": "没有安全可声明的整段NO；全窗由于具体讲述意义未知保持U，不强行制造非空K或NO。",
  "boundary_uncertainty": [
    {
      "segment_id": "S01",
      "label": "U",
      "global_seconds_exact": [
        "330",
        "35358656666666667/100000000000000"
      ],
      "title": "全窗连续人物近景的讲述意义",
      "visual_reason_or_unknown": "所有样本都是同一户外人物面部近景，嘴型与眼睑变化；没有音频/转录，是否包含必须保留的解释/结论无法判断。未见独立手势、工具操作、新物体或显著构图变化；不据此默认NO。",
      "evidence_frames": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04",
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
        "F23",
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
      "330",
      "3300297/10000"
    ],
    "end_bracket_exact": [
      "883883/2500",
      "35358656666666667/100000000000000"
    ],
    "interpretation": "窗口边缘极短未采样部分沿相邻可见状态提出初步建议；不声称已逐帧观察"
  },
  "unresolved_event_notes": [
    "无音频使整窗讲述的解释/结论价值未知；不能从口型编造台词。",
    "仅见人物面部近景，未见手势/工具操作/新结果；无需强行给出非空高光。"
  ],
  "missing_items": [],
  "read_image_inventory": [
    {
      "frame_id": "F00",
      "source_ordinal": 9891,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F00_O009891.png",
      "global_seconds_exact": "3300297/10000",
      "local_seconds_exact": "297/10000",
      "png_sha256": "3dbfaa7ebd5d3e30008066db7f4339d9ecbb34524d13e7ef1d2a8737a58c1974",
      "rgb_pixel_sha256": "88d6126242d65b8c31804b2d6950b7a446496a200d332a5202c2c941a9d85cab",
      "actual_png_sha256": "3dbfaa7ebd5d3e30008066db7f4339d9ecbb34524d13e7ef1d2a8737a58c1974",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 9902,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F01_O009902.png",
      "global_seconds_exact": "4955951/15000",
      "local_seconds_exact": "5951/15000",
      "png_sha256": "95e4024d863c22a1fb3562fa5d83e55cc79ac0b66886ab1a1acec32d7581ad19",
      "rgb_pixel_sha256": "192fe856c3dab39dd6aecf443597cacdd6b160e1ae807f908fe2a9b3e1a24cda",
      "actual_png_sha256": "95e4024d863c22a1fb3562fa5d83e55cc79ac0b66886ab1a1acec32d7581ad19",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 9913,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F02_O009913.png",
      "global_seconds_exact": "9922913/30000",
      "local_seconds_exact": "22913/30000",
      "png_sha256": "ab2eb61924d69e30cc9fbd9cff0297f8c23a39fa3ce9d0b4bf0b8a0118c8b7eb",
      "rgb_pixel_sha256": "137712fb65e3dfa8ee044d38ea5cbe89b6f63011c136465d3b72509035606489",
      "actual_png_sha256": "ab2eb61924d69e30cc9fbd9cff0297f8c23a39fa3ce9d0b4bf0b8a0118c8b7eb",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 9924,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F03_O009924.png",
      "global_seconds_exact": "827827/2500",
      "local_seconds_exact": "2827/2500",
      "png_sha256": "e17888f255b527f1b24a860b117241cf2953fb53e95700b6ba2e238bbd456800",
      "rgb_pixel_sha256": "d35612752a3087e7fe4a36ff303d830c6cd1ac8fae4df2bb0c3546fcaabbb188",
      "actual_png_sha256": "e17888f255b527f1b24a860b117241cf2953fb53e95700b6ba2e238bbd456800",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 9935,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F04_O009935.png",
      "global_seconds_exact": "1988987/6000",
      "local_seconds_exact": "8987/6000",
      "png_sha256": "427a85970acb45b72aa9c2879e9cf25ad6686135b73e8c68adcc0ac70c53cf5c",
      "rgb_pixel_sha256": "015ccfec4d3da98739e222f618ba4888129200e6469f21ae8ad9f10f462fd87d",
      "actual_png_sha256": "427a85970acb45b72aa9c2879e9cf25ad6686135b73e8c68adcc0ac70c53cf5c",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 9946,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F05_O009946.png",
      "global_seconds_exact": "4977973/15000",
      "local_seconds_exact": "27973/15000",
      "png_sha256": "3c20be1652d0129ded35a53b2b039ac97654b2b9eb0e0bf8ded26ed5cee51bce",
      "rgb_pixel_sha256": "064fdad6dc07d9357e26e4e8ec91d3c3f60379d5c978d34f73eb35fca7e56c18",
      "actual_png_sha256": "3c20be1652d0129ded35a53b2b039ac97654b2b9eb0e0bf8ded26ed5cee51bce",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 9958,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F06_O009958.png",
      "global_seconds_exact": "4983979/15000",
      "local_seconds_exact": "33979/15000",
      "png_sha256": "1e15133a0f02bf933fbc4b038e691a993530dc96b45fdd820c131da57125b3c7",
      "rgb_pixel_sha256": "9739d215194d304e909018abe00af88e11547f7203e38df36dab14a34bd1bce9",
      "actual_png_sha256": "1e15133a0f02bf933fbc4b038e691a993530dc96b45fdd820c131da57125b3c7",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 9969,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F07_O009969.png",
      "global_seconds_exact": "3326323/10000",
      "local_seconds_exact": "26323/10000",
      "png_sha256": "8c644ec4e82e78682a53cfb5acbfce206d5a77477264444dfdb8d0164ce4b2c1",
      "rgb_pixel_sha256": "8b7b07aa0acb8389e6b37e0ffae0f71eb5f25fc9824b92ccb0d437df0d88e6d0",
      "actual_png_sha256": "8c644ec4e82e78682a53cfb5acbfce206d5a77477264444dfdb8d0164ce4b2c1",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9980,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F08_O009980.png",
      "global_seconds_exact": "499499/1500",
      "local_seconds_exact": "4499/1500",
      "png_sha256": "f8774ffa6d69d92556c4d3d684a6b86abe00e9b13c694082656ee594cf564bb9",
      "rgb_pixel_sha256": "cefd6ef74a5472cafa4d32bca646797f12e17f217cfaea712bb8d6477d8349f0",
      "actual_png_sha256": "f8774ffa6d69d92556c4d3d684a6b86abe00e9b13c694082656ee594cf564bb9",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 9991,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F09_O009991.png",
      "global_seconds_exact": "10000991/30000",
      "local_seconds_exact": "100991/30000",
      "png_sha256": "9d7c9ff646979551bd7f2e68f082ad34b347b7a92a8e2b13e2b28a1b74face94",
      "rgb_pixel_sha256": "84e14573eb12b3719d9fef538785c0677c923f6c0f07e7fab446a5bf23c29399",
      "actual_png_sha256": "9d7c9ff646979551bd7f2e68f082ad34b347b7a92a8e2b13e2b28a1b74face94",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 10002,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F10_O010002.png",
      "global_seconds_exact": "1668667/5000",
      "local_seconds_exact": "18667/5000",
      "png_sha256": "9393f0946656884e52bfc38a1df4010490a3885f9510ce5d2d26322f76ea011f",
      "rgb_pixel_sha256": "b885469720f1b24a7691c743d7e5baee60f927ff675167de4afbbcd8fe01c37d",
      "actual_png_sha256": "9393f0946656884e52bfc38a1df4010490a3885f9510ce5d2d26322f76ea011f",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 10014,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F11_O010014.png",
      "global_seconds_exact": "1670669/5000",
      "local_seconds_exact": "20669/5000",
      "png_sha256": "c5cd55e40df94e11a2e3bb890e0b07b75e7408c52c48d5a9d8bd40689a4492b9",
      "rgb_pixel_sha256": "ff1ce8d19ded1485ebeb1598cbe89ac42261599ae14c8e7f755ba48b4ffdb2f1",
      "actual_png_sha256": "c5cd55e40df94e11a2e3bb890e0b07b75e7408c52c48d5a9d8bd40689a4492b9",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 10025,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F12_O010025.png",
      "global_seconds_exact": "401401/1200",
      "local_seconds_exact": "5401/1200",
      "png_sha256": "5c4cfd18e6aed7cdbec9d6b393722fb0921d758911a34f73823dd9ab20ed5ad3",
      "rgb_pixel_sha256": "605c96564fe04397b9f0c5c59eafc0f363bbda3a90c7efa276dd4d4c82d7c050",
      "actual_png_sha256": "5c4cfd18e6aed7cdbec9d6b393722fb0921d758911a34f73823dd9ab20ed5ad3",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 10036,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F13_O010036.png",
      "global_seconds_exact": "2511509/7500",
      "local_seconds_exact": "36509/7500",
      "png_sha256": "f92b0480db58499af47aafffb2cdaf67b8bf8bea8e079d16b8c2cdae8faaf512",
      "rgb_pixel_sha256": "484dbd807861eb58db6813377a6c09ef68190d7595a422ad325246d78548692d",
      "actual_png_sha256": "f92b0480db58499af47aafffb2cdaf67b8bf8bea8e079d16b8c2cdae8faaf512",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 10047,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F14_O010047.png",
      "global_seconds_exact": "3352349/10000",
      "local_seconds_exact": "52349/10000",
      "png_sha256": "e0dee4107e4902f12f63b8a4be0a8e263728512fc2dabdb1c545ddfce9082ebb",
      "rgb_pixel_sha256": "16dd6346cbdf16563890646637f12a625ca1fb6fe921f58e949f2cc7457f2e39",
      "actual_png_sha256": "e0dee4107e4902f12f63b8a4be0a8e263728512fc2dabdb1c545ddfce9082ebb",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 10058,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F15_O010058.png",
      "global_seconds_exact": "5034029/15000",
      "local_seconds_exact": "84029/15000",
      "png_sha256": "83a6b1c0f7afda350299d76aec328d1d23a3f8f650f2ea77dfe54c5995dfcacf",
      "rgb_pixel_sha256": "ba28e9b901dac57791c16c6410a2b181a32e3764050d8c81e5e843b78066bbf2",
      "actual_png_sha256": "83a6b1c0f7afda350299d76aec328d1d23a3f8f650f2ea77dfe54c5995dfcacf",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 10070,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F16_O010070.png",
      "global_seconds_exact": "1008007/3000",
      "local_seconds_exact": "18007/3000",
      "png_sha256": "fa112b3d4caa09a5f7cd5de83cf341c4c48b51604f439954cf1ae0b9d3afbb27",
      "rgb_pixel_sha256": "05c86f3ffd9b332d449c91dda8c0bc19591e37761b6fa63da7b60778363a3805",
      "actual_png_sha256": "fa112b3d4caa09a5f7cd5de83cf341c4c48b51604f439954cf1ae0b9d3afbb27",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 10081,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F17_O010081.png",
      "global_seconds_exact": "10091081/30000",
      "local_seconds_exact": "191081/30000",
      "png_sha256": "01373586acd3eb41c14db686dbaa9570d1f6782e73cd765ffb7c5bc79fe23085",
      "rgb_pixel_sha256": "7ba13b7d86a66d91c989032e95a1ce69bd9b7a6e92a755b9d1dc68028ea38c6d",
      "actual_png_sha256": "01373586acd3eb41c14db686dbaa9570d1f6782e73cd765ffb7c5bc79fe23085",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 10092,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F18_O010092.png",
      "global_seconds_exact": "841841/2500",
      "local_seconds_exact": "16841/2500",
      "png_sha256": "d907a8a86b71040cc7e35dc05a85019277a7ff1e53965a95a44472fbeca57910",
      "rgb_pixel_sha256": "2593a82a5a9d531322a4d097e2cbe444919ba253dbe35d0ae6b679a14fab060b",
      "actual_png_sha256": "d907a8a86b71040cc7e35dc05a85019277a7ff1e53965a95a44472fbeca57910",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 10103,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F19_O010103.png",
      "global_seconds_exact": "10113103/30000",
      "local_seconds_exact": "213103/30000",
      "png_sha256": "c215976c27317449a26fdad7dd5b24ae86b0dab55c5c759d15da79c0b10f4668",
      "rgb_pixel_sha256": "6a4b372c27736fd7cbfe4f85e732919cb920004004a7bd496e81f96b8ac577ea",
      "actual_png_sha256": "c215976c27317449a26fdad7dd5b24ae86b0dab55c5c759d15da79c0b10f4668",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 10114,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F20_O010114.png",
      "global_seconds_exact": "5062057/15000",
      "local_seconds_exact": "112057/15000",
      "png_sha256": "451e8789caa9834db2dbaff88d1956dc614b690b2767aeaa9e7491c1041e5b6e",
      "rgb_pixel_sha256": "d65961c0eee252a7802fded4b82b99c86986f8dd97166ed0d4e5bfa1764ccfe2",
      "actual_png_sha256": "451e8789caa9834db2dbaff88d1956dc614b690b2767aeaa9e7491c1041e5b6e",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 10126,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F21_O010126.png",
      "global_seconds_exact": "5068063/15000",
      "local_seconds_exact": "118063/15000",
      "png_sha256": "049e239687c92d73cb62038e32248097703308a25ee6459c9ab07d7fda054db5",
      "rgb_pixel_sha256": "bd6b48a5b3fac831fcfdbd8a6bfa18dd9e4d74226e119f4d17ffea8d434f8536",
      "actual_png_sha256": "049e239687c92d73cb62038e32248097703308a25ee6459c9ab07d7fda054db5",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 10137,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F22_O010137.png",
      "global_seconds_exact": "3382379/10000",
      "local_seconds_exact": "82379/10000",
      "png_sha256": "a2ab07f7c5a695e1c4d706ac4857fb29bdcc034809e5f9bdc0997a591c76aaf4",
      "rgb_pixel_sha256": "2c3e79479fe0784dab1aa855c9ee77420db85ffad31e1e913a6bec57f48ca97f",
      "actual_png_sha256": "a2ab07f7c5a695e1c4d706ac4857fb29bdcc034809e5f9bdc0997a591c76aaf4",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 10148,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F23_O010148.png",
      "global_seconds_exact": "2539537/7500",
      "local_seconds_exact": "64537/7500",
      "png_sha256": "5ca5970d3b2aefd9787494f8d1316062f5dfac5e413cf382163313c64d9f1fc4",
      "rgb_pixel_sha256": "b970d28e7d287e677443b13f8359a7f549a6b509caca7e049e2554f2b8ac1579",
      "actual_png_sha256": "5ca5970d3b2aefd9787494f8d1316062f5dfac5e413cf382163313c64d9f1fc4",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 10159,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F24_O010159.png",
      "global_seconds_exact": "10169159/30000",
      "local_seconds_exact": "269159/30000",
      "png_sha256": "a72f7a9dc66e70e9bf6e479b437341fac5de28f056213a37262d55e2867b0a50",
      "rgb_pixel_sha256": "0c654e236fabbf2f0e7f8b614e9da745cc8a792bbbbb677f8c3520ea84a090f4",
      "actual_png_sha256": "a72f7a9dc66e70e9bf6e479b437341fac5de28f056213a37262d55e2867b0a50",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 10170,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F25_O010170.png",
      "global_seconds_exact": "339339/1000",
      "local_seconds_exact": "9339/1000",
      "png_sha256": "1e0c00a68b8ae8dcfdfda95b8ab7194dcc5f15dd6d3a7beb3b37bc4d41bc5f44",
      "rgb_pixel_sha256": "84be6c5d72a7032935aa22a9515f845905cd90f8750ee01f9f2bb90fb9294828",
      "actual_png_sha256": "1e0c00a68b8ae8dcfdfda95b8ab7194dcc5f15dd6d3a7beb3b37bc4d41bc5f44",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 10181,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F26_O010181.png",
      "global_seconds_exact": "10191181/30000",
      "local_seconds_exact": "291181/30000",
      "png_sha256": "717e90389e2731ac7278cbe44396b81f8819a02134b7eaef3ef6b5a93debd923",
      "rgb_pixel_sha256": "d0503ca265c598ce346f085524bfaa7010c9ba9f13cb2f1fbcf6a0ee9d9ead7c",
      "actual_png_sha256": "717e90389e2731ac7278cbe44396b81f8819a02134b7eaef3ef6b5a93debd923",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 10193,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F27_O010193.png",
      "global_seconds_exact": "10203193/30000",
      "local_seconds_exact": "303193/30000",
      "png_sha256": "743807310d2ac8353dc2176f8f7d1e33a866b374690f0b1344d19d0a98853292",
      "rgb_pixel_sha256": "7bce76fcaafcd57136f880f6565a9348fae6ba40cd80ea543c292bccf4ea9d86",
      "actual_png_sha256": "743807310d2ac8353dc2176f8f7d1e33a866b374690f0b1344d19d0a98853292",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 10204,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F28_O010204.png",
      "global_seconds_exact": "2553551/7500",
      "local_seconds_exact": "78551/7500",
      "png_sha256": "e04b5f77d04a42c6a965b3e60ccaa10dae557f6b6ddc3dba88f509a55b3dad73",
      "rgb_pixel_sha256": "1f6d07f0d36e075eeb4a57d70575d914b8404a526ba68d0d4122b98be0081365",
      "actual_png_sha256": "e04b5f77d04a42c6a965b3e60ccaa10dae557f6b6ddc3dba88f509a55b3dad73",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 10215,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F29_O010215.png",
      "global_seconds_exact": "681681/2000",
      "local_seconds_exact": "21681/2000",
      "png_sha256": "89a50dcd310413d185233ac30ee0899fa909336c0317f7e3c138463b1944aada",
      "rgb_pixel_sha256": "c4f34232195467c716d03300a5d19d35369a845207ae21b721300362be5d0d6c",
      "actual_png_sha256": "89a50dcd310413d185233ac30ee0899fa909336c0317f7e3c138463b1944aada",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 10226,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F30_O010226.png",
      "global_seconds_exact": "5118113/15000",
      "local_seconds_exact": "168113/15000",
      "png_sha256": "32c044f5ffec0baf367995af0e7dcda462b2e52522bff7e74c402cc364203ac9",
      "rgb_pixel_sha256": "c68a34f172da7ca79032d159fbd0cdbeb8ad4b9527c371f4fc110fb1dfa8ca14",
      "actual_png_sha256": "32c044f5ffec0baf367995af0e7dcda462b2e52522bff7e74c402cc364203ac9",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 10237,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F31_O010237.png",
      "global_seconds_exact": "10247237/30000",
      "local_seconds_exact": "347237/30000",
      "png_sha256": "9ff9ac4e7c072e07a17aaa90092c72d74ac51fa67d986d9d239509461c2d9fe5",
      "rgb_pixel_sha256": "c4f9c7ad20c3504dd53af29c5372157287047a391fa527abba3fa394e34dc8af",
      "actual_png_sha256": "9ff9ac4e7c072e07a17aaa90092c72d74ac51fa67d986d9d239509461c2d9fe5",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 10249,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F32_O010249.png",
      "global_seconds_exact": "10259249/30000",
      "local_seconds_exact": "359249/30000",
      "png_sha256": "d14d9551358b45eb6a795ee1dac1ad1ec51a035e5ff9eadb2f69f41bc4c879c0",
      "rgb_pixel_sha256": "9c7ac8e5d9a02ae6e97ec6eb22097a693616e3a89bd5c91e86b81f7b52d6edf1",
      "actual_png_sha256": "d14d9551358b45eb6a795ee1dac1ad1ec51a035e5ff9eadb2f69f41bc4c879c0",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 10260,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F33_O010260.png",
      "global_seconds_exact": "171171/500",
      "local_seconds_exact": "6171/500",
      "png_sha256": "b0c37467bbcdac1eaad5e83113acb6c6fd7fd7e92b0f50b783501c9ae8e86b07",
      "rgb_pixel_sha256": "af21d28381a41dfad1ee5b437df14f9ea42bbb7f1fe701619ddd36972f595d6c",
      "actual_png_sha256": "b0c37467bbcdac1eaad5e83113acb6c6fd7fd7e92b0f50b783501c9ae8e86b07",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 10271,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F34_O010271.png",
      "global_seconds_exact": "10281271/30000",
      "local_seconds_exact": "381271/30000",
      "png_sha256": "4051870ad62d419381403cc995c2846d570de3064cc44e7f74c1f3250236a32c",
      "rgb_pixel_sha256": "08a4f68e396b88cdaacffe62133f4331ce5dc3b2a8840b87ee9c613fef3ed1b6",
      "actual_png_sha256": "4051870ad62d419381403cc995c2846d570de3064cc44e7f74c1f3250236a32c",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 10282,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F35_O010282.png",
      "global_seconds_exact": "5146141/15000",
      "local_seconds_exact": "196141/15000",
      "png_sha256": "4d04d3b4e3da5efe53f21c9afcb93f166f34c08cfe606e572efcdbb81a264811",
      "rgb_pixel_sha256": "475d5cb0494172ce0600a50b5a2fbb563840fa4b559949464902b45fb7691cc8",
      "actual_png_sha256": "4d04d3b4e3da5efe53f21c9afcb93f166f34c08cfe606e572efcdbb81a264811",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 10293,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F36_O010293.png",
      "global_seconds_exact": "3434431/10000",
      "local_seconds_exact": "134431/10000",
      "png_sha256": "e2ebb9c6053df56fc16814fc20c685835d0d27b1db4fa9edc599ca20cca29524",
      "rgb_pixel_sha256": "832fea2b97d5e6e2b1af12b4ec43a46b25d38b1e4f810910e702c33eeaf93d2c",
      "actual_png_sha256": "e2ebb9c6053df56fc16814fc20c685835d0d27b1db4fa9edc599ca20cca29524",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 10305,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F37_O010305.png",
      "global_seconds_exact": "687687/2000",
      "local_seconds_exact": "27687/2000",
      "png_sha256": "473207656b1a989c0359f46b655eadae7e008aea95745b694ae3613ff5efd282",
      "rgb_pixel_sha256": "4285a8b72aa163e5d31125e83c349b4df07dc09b70fd72c3d24b6dcc390e9056",
      "actual_png_sha256": "473207656b1a989c0359f46b655eadae7e008aea95745b694ae3613ff5efd282",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 10316,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F38_O010316.png",
      "global_seconds_exact": "2581579/7500",
      "local_seconds_exact": "106579/7500",
      "png_sha256": "92aefbffe0fd38df2f0e8b0e603aca663447939389bf0d7175b1b6ca0ddeabfd",
      "rgb_pixel_sha256": "780d31a21129257d9bd13a0df93b2e8be81b262b44bec7677748681ef4a83292",
      "actual_png_sha256": "92aefbffe0fd38df2f0e8b0e603aca663447939389bf0d7175b1b6ca0ddeabfd",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 10327,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F39_O010327.png",
      "global_seconds_exact": "10337327/30000",
      "local_seconds_exact": "437327/30000",
      "png_sha256": "7d256ce9bd908e63970eea41302b440eab73ff7f336c09a70118d7844a2c096e",
      "rgb_pixel_sha256": "ba16be70a0e7d5476d410099544f0dc005a041dff02de9b89f1a5c6f97918695",
      "actual_png_sha256": "7d256ce9bd908e63970eea41302b440eab73ff7f336c09a70118d7844a2c096e",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 10338,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F40_O010338.png",
      "global_seconds_exact": "1724723/5000",
      "local_seconds_exact": "74723/5000",
      "png_sha256": "2a01ff9eed40d504739ea664037d35520eb3510000d1e171d260a49039b2dce4",
      "rgb_pixel_sha256": "8afa2517ea2e04c835e8c4096a04fe84c8a36cedfdb73bea30602807d2a00a86",
      "actual_png_sha256": "2a01ff9eed40d504739ea664037d35520eb3510000d1e171d260a49039b2dce4",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 10349,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F41_O010349.png",
      "global_seconds_exact": "10359349/30000",
      "local_seconds_exact": "459349/30000",
      "png_sha256": "d04916776c87a19bb4e623c0d303d8d0f1183903cd95f87d0985f675d09641fd",
      "rgb_pixel_sha256": "39553675e28599de1c95709b74915828c3f8e52a27929a2f522a044f2744b903",
      "actual_png_sha256": "d04916776c87a19bb4e623c0d303d8d0f1183903cd95f87d0985f675d09641fd",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 10361,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F42_O010361.png",
      "global_seconds_exact": "10371361/30000",
      "local_seconds_exact": "471361/30000",
      "png_sha256": "acdd28796c4f2214aa9c955033313f59bbc3ec7149dce82dca61c1a30c5ddc0c",
      "rgb_pixel_sha256": "07c25216d9d62b71ef6d3d48f4793b04ff3339f32eabee382b6b214d1f48268e",
      "actual_png_sha256": "acdd28796c4f2214aa9c955033313f59bbc3ec7149dce82dca61c1a30c5ddc0c",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 10372,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F43_O010372.png",
      "global_seconds_exact": "2595593/7500",
      "local_seconds_exact": "120593/7500",
      "png_sha256": "d0edd158047f0b7a4548f9c65e849b7973bbc37cad431ab89efb8bba709a2f6d",
      "rgb_pixel_sha256": "b9f038a8bae0d4b02569dbdc8dbb8e60020fa0dca84592232ccec1fabc309de9",
      "actual_png_sha256": "d0edd158047f0b7a4548f9c65e849b7973bbc37cad431ab89efb8bba709a2f6d",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 10383,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F44_O010383.png",
      "global_seconds_exact": "3464461/10000",
      "local_seconds_exact": "164461/10000",
      "png_sha256": "9d9f4f3e45a89ddb32643fcaa0aef4e05fad669decc99743c574ef4d932fc879",
      "rgb_pixel_sha256": "71300f3f83442ac1c206bfd3431a0741449e6273e76a4a5e80b58148fa869b1e",
      "actual_png_sha256": "9d9f4f3e45a89ddb32643fcaa0aef4e05fad669decc99743c574ef4d932fc879",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 10394,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F45_O010394.png",
      "global_seconds_exact": "5202197/15000",
      "local_seconds_exact": "252197/15000",
      "png_sha256": "3a38f44e0084fa2c0f61b3639f5bb7ed34ccf393c91bd3a9181e04cc4a766780",
      "rgb_pixel_sha256": "db31614917bfa63ff2b10ac84af9f8f7e7fe8299915eed8a666f12223a430468",
      "actual_png_sha256": "3a38f44e0084fa2c0f61b3639f5bb7ed34ccf393c91bd3a9181e04cc4a766780",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 10405,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F46_O010405.png",
      "global_seconds_exact": "2083081/6000",
      "local_seconds_exact": "103081/6000",
      "png_sha256": "ed5358ccc9c338fdae371dbcecd359972a6c6a9697f54768207136247ef4550b",
      "rgb_pixel_sha256": "f48e2455d14ccd0e4acd6385f753e888d421b855efa00f15c61ce714e596a0cc",
      "actual_png_sha256": "ed5358ccc9c338fdae371dbcecd359972a6c6a9697f54768207136247ef4550b",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 10416,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F47_O010416.png",
      "global_seconds_exact": "217217/625",
      "local_seconds_exact": "10967/625",
      "png_sha256": "bef8fce62ab997d25add79147264fe547079ef9ccbe96dde0b77a5ca4fcf2eda",
      "rgb_pixel_sha256": "e6093d21a3682ec3dc7661f2b4f3963ae119fc44bea9a982c44538c0ad1194d1",
      "actual_png_sha256": "bef8fce62ab997d25add79147264fe547079ef9ccbe96dde0b77a5ca4fcf2eda",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 10428,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F48_O010428.png",
      "global_seconds_exact": "869869/2500",
      "local_seconds_exact": "44869/2500",
      "png_sha256": "84444a80a7aab4d473f7a3d1539809cba8077ec8d4e2ac3599bc817383e1c463",
      "rgb_pixel_sha256": "9e6de6d71eb7b260cffe0189263e123ab992f0f03f4d1673cb422f6cc16561d4",
      "actual_png_sha256": "84444a80a7aab4d473f7a3d1539809cba8077ec8d4e2ac3599bc817383e1c463",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 10439,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F49_O010439.png",
      "global_seconds_exact": "10449439/30000",
      "local_seconds_exact": "549439/30000",
      "png_sha256": "af167ce1c8ed70db58184d335e0070896721ebb091d7366b13d348db21d5133f",
      "rgb_pixel_sha256": "11377993d41cb35d524c937827719cb29a7938df41855cf2619b64ce47635a56",
      "actual_png_sha256": "af167ce1c8ed70db58184d335e0070896721ebb091d7366b13d348db21d5133f",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 10450,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F50_O010450.png",
      "global_seconds_exact": "209209/600",
      "local_seconds_exact": "11209/600",
      "png_sha256": "1297f8ebea6d7ed836211b215f85833588f688ba053075d5375d5856a3f906e4",
      "rgb_pixel_sha256": "10116b0ade854cd49966fb940a695d7ce4e8100494e4c156d847a5a617ee3302",
      "actual_png_sha256": "1297f8ebea6d7ed836211b215f85833588f688ba053075d5375d5856a3f906e4",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 10461,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F51_O010461.png",
      "global_seconds_exact": "3490487/10000",
      "local_seconds_exact": "190487/10000",
      "png_sha256": "ef2c650df030bef0d69bb73a6771b6d57c274cbf683b88f0de7915a3b7319bdd",
      "rgb_pixel_sha256": "067036e38c834092965657ed5dedc4a57d708007d2a3ec49a80375b3fbd71409",
      "actual_png_sha256": "ef2c650df030bef0d69bb73a6771b6d57c274cbf683b88f0de7915a3b7319bdd",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 10472,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F52_O010472.png",
      "global_seconds_exact": "1310309/3750",
      "local_seconds_exact": "72809/3750",
      "png_sha256": "74f0b46ba4f991ac188c9e5db352ce59fb8fed05e769288ddf8591368a9518ad",
      "rgb_pixel_sha256": "2591b13086815f596df263a11168fd1cc56591a7068957e755f26702cc7b0804",
      "actual_png_sha256": "74f0b46ba4f991ac188c9e5db352ce59fb8fed05e769288ddf8591368a9518ad",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 10484,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F53_O010484.png",
      "global_seconds_exact": "2623621/7500",
      "local_seconds_exact": "148621/7500",
      "png_sha256": "8ad891d985405efa2d9763db2c8cb675be621a7ae93df011e222a531bb9a4fe2",
      "rgb_pixel_sha256": "277939a45ba54e338f63480f635de68a286dbc7b0dcfe0c4f9b2df29b31f9be6",
      "actual_png_sha256": "8ad891d985405efa2d9763db2c8cb675be621a7ae93df011e222a531bb9a4fe2",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 10495,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F54_O010495.png",
      "global_seconds_exact": "2101099/6000",
      "local_seconds_exact": "121099/6000",
      "png_sha256": "0b95baa1923de5d663bac0e443ea868eb5ef08864dc89790a8c1287a323a15d7",
      "rgb_pixel_sha256": "2f21df22c250d867498310e42b1ce4cbeb5a2021b259e3cb4c50796d5a4b6f91",
      "actual_png_sha256": "0b95baa1923de5d663bac0e443ea868eb5ef08864dc89790a8c1287a323a15d7",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 10506,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F55_O010506.png",
      "global_seconds_exact": "1752751/5000",
      "local_seconds_exact": "102751/5000",
      "png_sha256": "3e1ae51a35faafa47f33f4e4ac625f936dee25dd0afb4b679c6c2a3e2185a325",
      "rgb_pixel_sha256": "8044ed9dae9cdb166eb7e6861189b1669c73f0434cf7587edeac45bccf08c48a",
      "actual_png_sha256": "3e1ae51a35faafa47f33f4e4ac625f936dee25dd0afb4b679c6c2a3e2185a325",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 10517,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F56_O010517.png",
      "global_seconds_exact": "10527517/30000",
      "local_seconds_exact": "627517/30000",
      "png_sha256": "333f3a72ee354b7e6a9b4b78c435c05032e617f0631f28faf063827f2830600c",
      "rgb_pixel_sha256": "9d960e5aa550696f7f06e4e7d198970a54f4e4c1ebaad9f23e5000dd851efe22",
      "actual_png_sha256": "333f3a72ee354b7e6a9b4b78c435c05032e617f0631f28faf063827f2830600c",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 10528,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F57_O010528.png",
      "global_seconds_exact": "658658/1875",
      "local_seconds_exact": "39908/1875",
      "png_sha256": "3a1931386e1255304c793ed0526569e0da6c31ee0366476d6e83458295599d29",
      "rgb_pixel_sha256": "c1370d647800c2ff1a1d32ca91cf8383d9b1ab740cb77d60a89d43d77d66f2d9",
      "actual_png_sha256": "3a1931386e1255304c793ed0526569e0da6c31ee0366476d6e83458295599d29",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 10540,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F58_O010540.png",
      "global_seconds_exact": "527527/1500",
      "local_seconds_exact": "32527/1500",
      "png_sha256": "cad0e90cb9e12804ec365e09ee094aceead10ba94b28a9d35394eb492af69776",
      "rgb_pixel_sha256": "28ecf0def9dbb389cadafe60229542b17aa38154990bb10125cae8c44812e9af",
      "actual_png_sha256": "cad0e90cb9e12804ec365e09ee094aceead10ba94b28a9d35394eb492af69776",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 10551,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F59_O010551.png",
      "global_seconds_exact": "3520517/10000",
      "local_seconds_exact": "220517/10000",
      "png_sha256": "c43191e97c9110e4e12bf53dc30aa1776787d3ecd5ffd49b2c85e71540cc0f97",
      "rgb_pixel_sha256": "ae27389181f67816e451d3687224c38d1210fe4a522157c55b64b1363f2eb936",
      "actual_png_sha256": "c43191e97c9110e4e12bf53dc30aa1776787d3ecd5ffd49b2c85e71540cc0f97",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 10562,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F60_O010562.png",
      "global_seconds_exact": "5286281/15000",
      "local_seconds_exact": "336281/15000",
      "png_sha256": "ffa3b74f3cd56b2d72242969930fc3aefb95561f3d80371be75ce7662a2ba87b",
      "rgb_pixel_sha256": "b8dfcbf09d6f523ae1e8481e56cafa7793d8d095acaf57d14df46e3435e28260",
      "actual_png_sha256": "ffa3b74f3cd56b2d72242969930fc3aefb95561f3d80371be75ce7662a2ba87b",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 10573,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F61_O010573.png",
      "global_seconds_exact": "10583573/30000",
      "local_seconds_exact": "683573/30000",
      "png_sha256": "80b99a67479b262200a3da23f8727886222d3ced4a9ab12eabe3518b87c1d6ea",
      "rgb_pixel_sha256": "838121b87b38cc0cc530cf18ffa5efc7aec974322d1f9dabd24217f68c77f5f6",
      "actual_png_sha256": "80b99a67479b262200a3da23f8727886222d3ced4a9ab12eabe3518b87c1d6ea",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 10584,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F62_O010584.png",
      "global_seconds_exact": "441441/1250",
      "local_seconds_exact": "28941/1250",
      "png_sha256": "090fdceed7387fcf4e19f47d6525b71eaacd9115902bf0da616d75d5f6a64d07",
      "rgb_pixel_sha256": "87b9e7c31e9b44d27d9720f13c4108dac18ca54d22f492688f5b15984b940ff9",
      "actual_png_sha256": "090fdceed7387fcf4e19f47d6525b71eaacd9115902bf0da616d75d5f6a64d07",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 10596,
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\frames\\F63_O010596.png",
      "global_seconds_exact": "883883/2500",
      "local_seconds_exact": "58883/2500",
      "png_sha256": "fab78409d2a95f59eee2fd37cadc5036c3fed87d57bc65573ebb94cc6ac1719b",
      "rgb_pixel_sha256": "f8de3206749029eb2538c74529df9dc0e280b84baf534269d8b9d33b14bf7938",
      "actual_png_sha256": "fab78409d2a95f59eee2fd37cadc5036c3fed87d57bc65573ebb94cc6ac1719b",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_fact": "灰发胡须人物在户外栅栏前面部近景，面向镜头偏侧，嘴型或眼睑有变化；背景为草地、白房与车辆局部，未见手或工具操作"
    }
  ]
}



## 完整新增公开证据：03_AwmHb44_ouw_W11.independent_initial_blind_v1.md
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\03_AwmHb44_ouw_W11.independent_initial_blind_v1.md
字节：1607；SHA256：1077f7e621c740bcea4bb5dd877afa455ed7b99e520b9c987454741d63d4146e

# AwmHb44_ouw:SLOT6:11 独立初始盲审

实际通过 view_image 读取 F00–F63 全部64张原始 PNG（8批，每批8张）；PNG SHA 全部与 manifest 匹配。仅使用本窗 manifest/frames，未读教师内容、旧标签、分数、模型预测、其他项目文件、overview、视频或音频。

声明窗口：330 — 35358656666666667/100000000000000 秒（源全局时钟）。K=0 段，NO=0 段，U=1 段；三类按半开区间互斥覆盖。以下是初步编辑建议，切点与失焦、无音频问题在 U 中保留。

| 类别 | 全局精确秒区间 | 建议/事实 | 理由 |
|---|---|---|---|
| U | 330 → 35358656666666667/100000000000000 | 全窗连续人物近景的讲述意义 | 所有样本都是同一户外人物面部近景，嘴型与眼睑变化；没有音频/转录，是否包含必须保留的解释/结论无法判断。未见独立手势、工具操作、新物体或显著构图变化；不据此默认NO。 |

未决事实：

- 无音频使整窗讲述的解释/结论价值未知；不能从口型编造台词。
- 仅见人物面部近景，未见手势/工具操作/新结果；无需强行给出非空高光。

每帧 frame_id、source_ordinal、exact PTS、PNG路径/期望与实际SHA、读图批次和事实见同名 JSON。有限floor64采样可能漏掉瞬时动作，稳定重复间隙没有机械转成U。源视频/完整native帧和实际processor有效视图未见。

student_processor_visibility_verified=false；training_admitted=false；full_native_frames_observed=false。这是独立初始盲审，不是金标或完整训练资格。



## 完整新增公开证据：manifest.json
来源：G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\supplements\risk01_kL_W02_local1to3\manifest.json
字节：31314；SHA256：69700fa505595d4e52d01f24d1daccea132435ffa60e92fa72f8162f52bf38fc

{
  "status": "NEW_NATIVE_OBSERVATION_RISK_TASK_01_NOT_A_LABEL",
  "task_kind": "BOUNDARY_ACTION_RISK",
  "planned_risk_task_number": 1,
  "risk_task_budget_max": 4,
  "window_id": "kLxoNp-UchI:SLOT6:2",
  "source_sha256": "0c91bfa880e3af0e1716e7456ada0a304a97911eef76b1cd4fdce5066a52e8f7",
  "source_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\kLxoNp-UchI\\kLxoNp-UchI.mp4",
  "manifest_sha256": "2544ad72c2c7b12c5204ca197cb9d5ee7904acb752822314e42edbf6fc1a0b6a",
  "global_domain_exact": [
    "61",
    "63"
  ],
  "local_domain_exact": [
    "1",
    "3"
  ],
  "frames": [
    {
      "frame_id": "R000",
      "source_ordinal": 1829,
      "global_seconds_exact": "1830829/30000",
      "window_local_seconds_exact": "30829/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R000_O001829.png",
      "png_sha256": "82cf0c4246f91378ed924adbeaded85e4377d7a455e45b3d5ae54bec5698c6a9",
      "rgb_pixel_sha256": "0e2f6f8c80e88813e59d305cd90fe7c65294f473bdac0cb5eccee1e208972e98"
    },
    {
      "frame_id": "R001",
      "source_ordinal": 1830,
      "global_seconds_exact": "61061/1000",
      "window_local_seconds_exact": "1061/1000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R001_O001830.png",
      "png_sha256": "54f78d9f604fc493a96938bf5b93210c867b0bf8c3892738c8942f695154529c",
      "rgb_pixel_sha256": "1da7caef78a4bdee65a44253f3514e47b523ee91c27a289a95f79324e125228c"
    },
    {
      "frame_id": "R002",
      "source_ordinal": 1831,
      "global_seconds_exact": "1832831/30000",
      "window_local_seconds_exact": "32831/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R002_O001831.png",
      "png_sha256": "b8a3199aaf17767599aa8b9dfb6e3123d6d21b1dcd50f9d51aeae8709ad8472f",
      "rgb_pixel_sha256": "12154433572c20f38f3604da7100cb3f03b6ea3f8c3ce3277cd8980f0ca0eea5"
    },
    {
      "frame_id": "R003",
      "source_ordinal": 1832,
      "global_seconds_exact": "229229/3750",
      "window_local_seconds_exact": "4229/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R003_O001832.png",
      "png_sha256": "0575687d2090bd1cccdcc2c1f22c126e767951de3f3b1ac96d3a145fee932599",
      "rgb_pixel_sha256": "4e2e8ed471469285469d049649ffb5b75fb25c8dc8485e4f69368d222f75f881"
    },
    {
      "frame_id": "R004",
      "source_ordinal": 1833,
      "global_seconds_exact": "611611/10000",
      "window_local_seconds_exact": "11611/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R004_O001833.png",
      "png_sha256": "1b31fe02991c521d8bd834e443ee2450faccb0e3ccec5d7c415e4cccf8d395b8",
      "rgb_pixel_sha256": "8cbdfab7659a82938fd30a04ce8325597b494241ed27de994f067b01b67741b8"
    },
    {
      "frame_id": "R005",
      "source_ordinal": 1834,
      "global_seconds_exact": "917917/15000",
      "window_local_seconds_exact": "17917/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R005_O001834.png",
      "png_sha256": "a55aacd763d055bb7271c77fdb2cea8502821c3f208a9fadeada5b54943d0983",
      "rgb_pixel_sha256": "30ce7ddc750d6cfd2248ce153dd9967f9fc1dbe80a5311f8907bbbed6420294d"
    },
    {
      "frame_id": "R006",
      "source_ordinal": 1835,
      "global_seconds_exact": "367367/6000",
      "window_local_seconds_exact": "7367/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R006_O001835.png",
      "png_sha256": "21329eea145f694b182486dcd5371f602cdf82bb332a5002e810d19023d61aaf",
      "rgb_pixel_sha256": "037c1c9e26806fb34f431252c759f6f5fe96154bab77a7ec3f02c3fb89bd30a7"
    },
    {
      "frame_id": "R007",
      "source_ordinal": 1836,
      "global_seconds_exact": "153153/2500",
      "window_local_seconds_exact": "3153/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R007_O001836.png",
      "png_sha256": "90e0f3aac28dbc157f15938818dd24c9b45def8a93c0dfa7328927fa9e1deecf",
      "rgb_pixel_sha256": "95784b93cfa8d6e7e8cacd710ed23dda74eb5c80bc57a7a731b05179d35fd166"
    },
    {
      "frame_id": "R008",
      "source_ordinal": 1837,
      "global_seconds_exact": "1838837/30000",
      "window_local_seconds_exact": "38837/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R008_O001837.png",
      "png_sha256": "4981c655598959afb9ccf272dbb013e4e9fbd69d2eb735817caa0b27aa28a91e",
      "rgb_pixel_sha256": "c7b6fbd4f8ca664ab6ca2a48992dd7316d586e824719fad53daa7f86848db711"
    },
    {
      "frame_id": "R009",
      "source_ordinal": 1838,
      "global_seconds_exact": "919919/15000",
      "window_local_seconds_exact": "19919/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R009_O001838.png",
      "png_sha256": "7d1adb02c55117cac10335c782972d000c24e2036be6f9cbfb0e8b09d70fbfda",
      "rgb_pixel_sha256": "148e8c7b9d21ee031903b1368ed756d4dc2a73a32e7a7247fd3fc694558deb5c"
    },
    {
      "frame_id": "R010",
      "source_ordinal": 1839,
      "global_seconds_exact": "613613/10000",
      "window_local_seconds_exact": "13613/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R010_O001839.png",
      "png_sha256": "679241e5e4089a52262600cfbbc0fe47831cc4e8c0d63c9bd091fd49b3ebdb83",
      "rgb_pixel_sha256": "ac32f6319c98e4356afe832afdbaf46a63394c7b272ac2b6b4faee57dcd9b8c7"
    },
    {
      "frame_id": "R011",
      "source_ordinal": 1840,
      "global_seconds_exact": "23023/375",
      "window_local_seconds_exact": "523/375",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R011_O001840.png",
      "png_sha256": "d7d752eb9bd369ffbf5b19912459d23134fca92229531e3f9c967a515bfefe0c",
      "rgb_pixel_sha256": "6c60be7381d511179466617deaab77160e2249e511e0838f392836bb9c6f3627"
    },
    {
      "frame_id": "R012",
      "source_ordinal": 1841,
      "global_seconds_exact": "1842841/30000",
      "window_local_seconds_exact": "42841/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R012_O001841.png",
      "png_sha256": "b756b7d1b4ce6ae57b7f3ce8437eb043e865e03ed5af1d44a3af9c8f47d31f0e",
      "rgb_pixel_sha256": "2254676776fd979603d7e65769591f10455b9edb7d10616c54d466999742d729"
    },
    {
      "frame_id": "R013",
      "source_ordinal": 1842,
      "global_seconds_exact": "307307/5000",
      "window_local_seconds_exact": "7307/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R013_O001842.png",
      "png_sha256": "8368599a47449b0110a50f50899172cae5cb2b1f7430e38678af6b3a33a74d19",
      "rgb_pixel_sha256": "9577f172a46b842c17c78c25d8c21bbf78dcecb80b5e98ca36abde0b89b89440"
    },
    {
      "frame_id": "R014",
      "source_ordinal": 1843,
      "global_seconds_exact": "1844843/30000",
      "window_local_seconds_exact": "44843/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R014_O001843.png",
      "png_sha256": "2da966c943e09d238f50729515f47ae7371e3a683f1a9d1b34a099a7535cd2aa",
      "rgb_pixel_sha256": "fa046324c67268ba719a7045b81c6140e4849b9768e93136cf6b1237d9f7105e"
    },
    {
      "frame_id": "R015",
      "source_ordinal": 1844,
      "global_seconds_exact": "461461/7500",
      "window_local_seconds_exact": "11461/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R015_O001844.png",
      "png_sha256": "04ebe2e2899b9068736751822b8ad7aa8cef97d7e84f003d5d3520fcffe664a6",
      "rgb_pixel_sha256": "df1885c3e4c899db5f87ee0d4d8bc92b7098dd195864a03c8734eb02c0fcda46"
    },
    {
      "frame_id": "R016",
      "source_ordinal": 1845,
      "global_seconds_exact": "123123/2000",
      "window_local_seconds_exact": "3123/2000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R016_O001845.png",
      "png_sha256": "4a2cb9e54ba6107d887edbf9c015e3ca312f43385c4d21f296fc93862678145a",
      "rgb_pixel_sha256": "55b77ac9b2e29800f5a7c07907f2c4b5f51274629543166707108ec888562465"
    },
    {
      "frame_id": "R017",
      "source_ordinal": 1846,
      "global_seconds_exact": "923923/15000",
      "window_local_seconds_exact": "23923/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R017_O001846.png",
      "png_sha256": "eb6671c4c2a8cd0a84c73c9e607e467068ab8301cad76de06cbc8feb9182f792",
      "rgb_pixel_sha256": "c8078caa0ed8283f799dcba53d239ad546558600301980ca44c239c71133a28a"
    },
    {
      "frame_id": "R018",
      "source_ordinal": 1847,
      "global_seconds_exact": "1848847/30000",
      "window_local_seconds_exact": "48847/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R018_O001847.png",
      "png_sha256": "1d11d314db08c69c4d9a9055ac852225ebc867d6b8469e7ddc08e366398d2a9c",
      "rgb_pixel_sha256": "44cbd7870cdd571dca6bedb794b0e0d331de6c9ab33dfafcaf478861338912c6"
    },
    {
      "frame_id": "R019",
      "source_ordinal": 1848,
      "global_seconds_exact": "77077/1250",
      "window_local_seconds_exact": "2077/1250",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R019_O001848.png",
      "png_sha256": "41c8c3e04f2c85d82ed8e2c4c7d26463e1cf236a99940f758da6c8494b2e16fa",
      "rgb_pixel_sha256": "d19d817354048949cec5e2ca3fe2181b2d3d4679d8040603a228786408573eda"
    },
    {
      "frame_id": "R020",
      "source_ordinal": 1849,
      "global_seconds_exact": "1850849/30000",
      "window_local_seconds_exact": "50849/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R020_O001849.png",
      "png_sha256": "9e3b8f70b6c638336a74ebdd72874c01d2fa93b86d9d67ba281f739093e2214d",
      "rgb_pixel_sha256": "89909285056715f0e662c2966340bd92f11cdf747e5ed0c2e87d529f1207ee6f"
    },
    {
      "frame_id": "R021",
      "source_ordinal": 1850,
      "global_seconds_exact": "37037/600",
      "window_local_seconds_exact": "1037/600",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R021_O001850.png",
      "png_sha256": "24c3c2788a6880eff258edf2583811ab2661c46a831d7707d761e4dbd1cccc94",
      "rgb_pixel_sha256": "a9b11b20e50630d7e959a04b7e17c415cb0c7e397b9a154a7cab1a3bb344dd43"
    },
    {
      "frame_id": "R022",
      "source_ordinal": 1851,
      "global_seconds_exact": "617617/10000",
      "window_local_seconds_exact": "17617/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R022_O001851.png",
      "png_sha256": "72eb078914b2e882d5d7ee0b2f044e4b7c972526b775386fff6d14afdfd06ea9",
      "rgb_pixel_sha256": "155459531875df6bf840c23c38da2b0a9db57f0a74cf095a770e07b88ac54d09"
    },
    {
      "frame_id": "R023",
      "source_ordinal": 1852,
      "global_seconds_exact": "463463/7500",
      "window_local_seconds_exact": "13463/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R023_O001852.png",
      "png_sha256": "b42c0a30a68e8bac9ca875258250ff12c315d9a49747c31b3632c51a43319f7f",
      "rgb_pixel_sha256": "e49b28f2ce2fd66fb488ea13ce45e401172dd75e7186806ab5dc9d9627ba708f"
    },
    {
      "frame_id": "R024",
      "source_ordinal": 1853,
      "global_seconds_exact": "1854853/30000",
      "window_local_seconds_exact": "54853/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R024_O001853.png",
      "png_sha256": "b9b6bd8db14ab2e6acdf7cbb4a70713838e4b4f4b77c14dc754de42b7412f22c",
      "rgb_pixel_sha256": "fafb8231e7138470d6b1f0e0f39c55f41ff313ad96ff0ee656c076723f46612b"
    },
    {
      "frame_id": "R025",
      "source_ordinal": 1854,
      "global_seconds_exact": "309309/5000",
      "window_local_seconds_exact": "9309/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R025_O001854.png",
      "png_sha256": "673b08fae3772c69d0db8a5b4e81908697ba2bba9f50bb056162bf9e158734cf",
      "rgb_pixel_sha256": "019c620a46b6cd49493accc717170328572cc12e280e69cefb0ac9718178af2a"
    },
    {
      "frame_id": "R026",
      "source_ordinal": 1855,
      "global_seconds_exact": "371371/6000",
      "window_local_seconds_exact": "11371/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R026_O001855.png",
      "png_sha256": "771e0a8a161233be8c4b53ecc35de921646b8af7654dd8a78864a79348fd4b3f",
      "rgb_pixel_sha256": "e0262554a0eeb3b59d0e4c0d3e99b72834561a92932e9fd1a23d1633925d6e66"
    },
    {
      "frame_id": "R027",
      "source_ordinal": 1856,
      "global_seconds_exact": "116116/1875",
      "window_local_seconds_exact": "3616/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R027_O001856.png",
      "png_sha256": "451a508a152f140e552e7931441d37dd4135118539f39be54ad5a7d8c02d5b9f",
      "rgb_pixel_sha256": "1fba3d68400bf7f3a94f8b21f172533be700a945437438a219c761e0e4a60900"
    },
    {
      "frame_id": "R028",
      "source_ordinal": 1857,
      "global_seconds_exact": "619619/10000",
      "window_local_seconds_exact": "19619/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R028_O001857.png",
      "png_sha256": "12f15f2859c2f9912f5893ef81908f13b5d559e5a6fa135a51253701dcf5ea0b",
      "rgb_pixel_sha256": "0df07de012db6034edb2c2dbd1caaef7cd8be1855f113de3835086358b1157e8"
    },
    {
      "frame_id": "R029",
      "source_ordinal": 1858,
      "global_seconds_exact": "929929/15000",
      "window_local_seconds_exact": "29929/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R029_O001858.png",
      "png_sha256": "337c3f7be353c97fa6933d50435f21a26e203bf0ca8b03b12191e6349f43d239",
      "rgb_pixel_sha256": "ce9521d2e7e7987641af6eeb91a265778b996cd87673b223eaad0b8baf865d89"
    },
    {
      "frame_id": "R030",
      "source_ordinal": 1859,
      "global_seconds_exact": "1860859/30000",
      "window_local_seconds_exact": "60859/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R030_O001859.png",
      "png_sha256": "ffcf9b4e39e30a92efb94f244714853324ecac5dbf1596c4b433ba78ef9771c6",
      "rgb_pixel_sha256": "eb9d80940e9d30ad4b68da04f0eca01811cfbdf4c071a505da7c334e894f9bf1"
    },
    {
      "frame_id": "R031",
      "source_ordinal": 1860,
      "global_seconds_exact": "31031/500",
      "window_local_seconds_exact": "1031/500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R031_O001860.png",
      "png_sha256": "c38798539784fab8c8a1ccb98dc2e4450539db3fea3ff731fe647096881a25c8",
      "rgb_pixel_sha256": "07b838adb561d4a3bd4ab570f0235e024aca3f14c23612e18d3166004ecbc32c"
    },
    {
      "frame_id": "R032",
      "source_ordinal": 1861,
      "global_seconds_exact": "1862861/30000",
      "window_local_seconds_exact": "62861/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R032_O001861.png",
      "png_sha256": "a7717f6d5797477ca4dacecf680284440f9aec4fc6096d7223b677b3c04facd4",
      "rgb_pixel_sha256": "c3ca0f82ff67cb2c8419b050613a984905d0e8c47ad721b8e36f7784da97d870"
    },
    {
      "frame_id": "R033",
      "source_ordinal": 1862,
      "global_seconds_exact": "931931/15000",
      "window_local_seconds_exact": "31931/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R033_O001862.png",
      "png_sha256": "75df9a49e8082a18c4274a2ce7f3aa79de5dea528e5550647713e24e6d684531",
      "rgb_pixel_sha256": "86cb2b9320d16f2fb30d9f613366917a7dbdf542896b2d2f4e13367ddfcb672f"
    },
    {
      "frame_id": "R034",
      "source_ordinal": 1863,
      "global_seconds_exact": "621621/10000",
      "window_local_seconds_exact": "21621/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R034_O001863.png",
      "png_sha256": "5a0e62f3c237b221543f960152f0cbae7d83bf83ba9c1838e8ca3ead73d7c53a",
      "rgb_pixel_sha256": "1b86dc6d9eac1993ab87511de3163ab92474e310ac638a2ef32ac2e45588268c"
    },
    {
      "frame_id": "R035",
      "source_ordinal": 1864,
      "global_seconds_exact": "233233/3750",
      "window_local_seconds_exact": "8233/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R035_O001864.png",
      "png_sha256": "387354d91a4d6c5598e05ab0b34da9c4ebdc23fb81a1b653b5101a53ec159640",
      "rgb_pixel_sha256": "36cdd74189f756fc6744d86141422149e5006deca52dc4d78c8804dd45414fff"
    },
    {
      "frame_id": "R036",
      "source_ordinal": 1865,
      "global_seconds_exact": "373373/6000",
      "window_local_seconds_exact": "13373/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R036_O001865.png",
      "png_sha256": "e3f0a24e1641e7f3ac8e172b67e1a1ef31686dce2e2981a106d10d973ea309fa",
      "rgb_pixel_sha256": "cddcd3d26a2b343e3c403ac9ae03824757c475ceaae952717d63fb40d50df33a"
    },
    {
      "frame_id": "R037",
      "source_ordinal": 1866,
      "global_seconds_exact": "311311/5000",
      "window_local_seconds_exact": "11311/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R037_O001866.png",
      "png_sha256": "371d229cce96fecbc3e39ccd10b8a6915b15f4fafd812fc8816b67df81b82cb8",
      "rgb_pixel_sha256": "4304d3ed2322d7f74a88b1bab6e20261ca3570b2a7d86fdc43becc229496982c"
    },
    {
      "frame_id": "R038",
      "source_ordinal": 1867,
      "global_seconds_exact": "1868867/30000",
      "window_local_seconds_exact": "68867/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R038_O001867.png",
      "png_sha256": "d34d28c68a22e3841c5158e1cba60d6b347e7177c551e235ab8a13a49077b068",
      "rgb_pixel_sha256": "84024764735160519f5cc2faf7d9239ad2dcfa11b95068a52540d88ff07e7d58"
    },
    {
      "frame_id": "R039",
      "source_ordinal": 1868,
      "global_seconds_exact": "467467/7500",
      "window_local_seconds_exact": "17467/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R039_O001868.png",
      "png_sha256": "2c02d301e4ae10a455fbfd56afc6a6667285922ddd1b46a83ee7397d4e0053fb",
      "rgb_pixel_sha256": "a6f44ab45dcc598a2126786abae8d483cf563e1ab9933bcf1129eb7e0015b4ac"
    },
    {
      "frame_id": "R040",
      "source_ordinal": 1869,
      "global_seconds_exact": "623623/10000",
      "window_local_seconds_exact": "23623/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R040_O001869.png",
      "png_sha256": "651ecaf823dfa72b83d2cf778d60c9fa8ee3be521130312a29444b789c99f255",
      "rgb_pixel_sha256": "72e64335461f8059515bfd78369065474fa686a5f2b7b0e4b59ec60e9b98cb51"
    },
    {
      "frame_id": "R041",
      "source_ordinal": 1870,
      "global_seconds_exact": "187187/3000",
      "window_local_seconds_exact": "7187/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R041_O001870.png",
      "png_sha256": "ee5bfb8d9e1433142de093d1ba22898bf300823038500e5f44503632cef87652",
      "rgb_pixel_sha256": "5092b38afd40c2d99a4c832ba021ff042a2bdce1b1c77d9bfa7a99b51dec3f3e"
    },
    {
      "frame_id": "R042",
      "source_ordinal": 1871,
      "global_seconds_exact": "1872871/30000",
      "window_local_seconds_exact": "72871/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R042_O001871.png",
      "png_sha256": "02e5d78f9642a04c43785d82551bea86769cdf99aa5871d48d50c15e436e327e",
      "rgb_pixel_sha256": "dbe24f2f8dac56f0e07b0cafa4b142f8372bff92c16f44b1a729c43dc3da232d"
    },
    {
      "frame_id": "R043",
      "source_ordinal": 1872,
      "global_seconds_exact": "39039/625",
      "window_local_seconds_exact": "1539/625",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R043_O001872.png",
      "png_sha256": "2bf20e23753234391665d702c1c64fcc71a7ecc8a3d84972da8f0335ca3740a1",
      "rgb_pixel_sha256": "71bb883a567a034ddbda9ccd1cc273bc668ff9372c8bf85b5d9cef4b07b492ac"
    },
    {
      "frame_id": "R044",
      "source_ordinal": 1873,
      "global_seconds_exact": "1874873/30000",
      "window_local_seconds_exact": "74873/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R044_O001873.png",
      "png_sha256": "c613926ff434f127bd7bb3ad4325918b3a0f9a9d8fe41e900b4e26d00ef46a65",
      "rgb_pixel_sha256": "bd5c342552943e298a88ef7d74b19ee291ad7fc68bee67215483ec54759f2aca"
    },
    {
      "frame_id": "R045",
      "source_ordinal": 1874,
      "global_seconds_exact": "937937/15000",
      "window_local_seconds_exact": "37937/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R045_O001874.png",
      "png_sha256": "248c2d15ad663962b58416ae8f728ed7dfe73311a9c5df6eebfb753b62527a10",
      "rgb_pixel_sha256": "4b3bada5360057aa8a8f93183dde3bba7eed071c42faf40b1227c982b07d810e"
    },
    {
      "frame_id": "R046",
      "source_ordinal": 1875,
      "global_seconds_exact": "1001/16",
      "window_local_seconds_exact": "41/16",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R046_O001875.png",
      "png_sha256": "7bac29cd246fa7120a310903b198dc9ea838179da95b92b41885885a258e2b95",
      "rgb_pixel_sha256": "46f5c21906d38e4a5a83db7e7ce56819c79495843701abb611e9943f372a8801"
    },
    {
      "frame_id": "R047",
      "source_ordinal": 1876,
      "global_seconds_exact": "469469/7500",
      "window_local_seconds_exact": "19469/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R047_O001876.png",
      "png_sha256": "21863c67a9ffbd2478cdab723f524f4e8534458a350ec5086ce3c55d16b0e51f",
      "rgb_pixel_sha256": "49a62821347c5fa7315df51d7993f86e876756cd0f8b94d7a9269a7ac98e9e71"
    },
    {
      "frame_id": "R048",
      "source_ordinal": 1877,
      "global_seconds_exact": "1878877/30000",
      "window_local_seconds_exact": "78877/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R048_O001877.png",
      "png_sha256": "b059de8927574251cd42f15efde14a3ae35be789635057451a97b4b7e9446673",
      "rgb_pixel_sha256": "0f05d36344f82e396f2243e7e0e949dad54de18270c8af368b23764c36ef0402"
    },
    {
      "frame_id": "R049",
      "source_ordinal": 1878,
      "global_seconds_exact": "313313/5000",
      "window_local_seconds_exact": "13313/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R049_O001878.png",
      "png_sha256": "725099f8c0f1c2797020a8ee9914547b1eaadc37a8733b6687b36757c8883b6c",
      "rgb_pixel_sha256": "86b172d5091ca7d93ca29df8d35b10da2d7da5f21cdf54584f2299c7763ec98d"
    },
    {
      "frame_id": "R050",
      "source_ordinal": 1879,
      "global_seconds_exact": "1880879/30000",
      "window_local_seconds_exact": "80879/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R050_O001879.png",
      "png_sha256": "3ff67b2a8ef9e858235f9967dee1fa5fb798965ff3f120df5839a5bc05524d68",
      "rgb_pixel_sha256": "639e5cffc770311034651674d48c4ef4f4fb9333ec38625016ef60c575980159"
    },
    {
      "frame_id": "R051",
      "source_ordinal": 1880,
      "global_seconds_exact": "47047/750",
      "window_local_seconds_exact": "2047/750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R051_O001880.png",
      "png_sha256": "c938c81f2b199e0b3cfbc2c98ffede6147d4ec07e84e6ecafd1da65abf2d6fb7",
      "rgb_pixel_sha256": "41658c76662b17c2ccfb7d50d2b897d95114cc346d591089a324c4c7e3ffc164"
    },
    {
      "frame_id": "R052",
      "source_ordinal": 1881,
      "global_seconds_exact": "627627/10000",
      "window_local_seconds_exact": "27627/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R052_O001881.png",
      "png_sha256": "264e8c38362f3f3a3df7bb022493d28d9bfd6d736bd8c709ea33db8c5db2b580",
      "rgb_pixel_sha256": "11f8e91e0d5d4ee95ee5856bd2713aa111e34dd84dccf4d065cf3e35a89784aa"
    },
    {
      "frame_id": "R053",
      "source_ordinal": 1882,
      "global_seconds_exact": "941941/15000",
      "window_local_seconds_exact": "41941/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R053_O001882.png",
      "png_sha256": "aebad0189e2d8b632400dca8a7b772c4cb9826cc97a27d9e9efa5549013ab2d1",
      "rgb_pixel_sha256": "dd5e37ce37b5dc33bf304d6929d9223515c0b5e1623f228987d2ed9d33025160"
    },
    {
      "frame_id": "R054",
      "source_ordinal": 1883,
      "global_seconds_exact": "1884883/30000",
      "window_local_seconds_exact": "84883/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R054_O001883.png",
      "png_sha256": "e3148bce1c1b5519e20b776c36c5b66d42804abd9e8dc0605ff7179ca4d984c1",
      "rgb_pixel_sha256": "91202f886a8256cbdd8503f42e1e3de5945c0cea1d16a90e9645b83e243be31f"
    },
    {
      "frame_id": "R055",
      "source_ordinal": 1884,
      "global_seconds_exact": "157157/2500",
      "window_local_seconds_exact": "7157/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R055_O001884.png",
      "png_sha256": "d83b433e003442d8eee7bcbd589a175112897638487fba226af53a2e78b8c3df",
      "rgb_pixel_sha256": "1069690fc487ee114b0d0d0d2d0dd9fdd7c97f6d2ff11bee13ee611a10abaf0c"
    },
    {
      "frame_id": "R056",
      "source_ordinal": 1885,
      "global_seconds_exact": "377377/6000",
      "window_local_seconds_exact": "17377/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R056_O001885.png",
      "png_sha256": "69e0ff3b3a1fb98c35f69026e24839a784310117aea94dd5b458af4ace94890c",
      "rgb_pixel_sha256": "a4436b3f23b27ba1305b2ce46277d68f0f01bf3c74b157831e7012c80586a493"
    },
    {
      "frame_id": "R057",
      "source_ordinal": 1886,
      "global_seconds_exact": "943943/15000",
      "window_local_seconds_exact": "43943/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R057_O001886.png",
      "png_sha256": "3aaec3c5f2d2327619ed52ba128122ccdfac25058d6798b59fa468c018ad009b",
      "rgb_pixel_sha256": "396bd87e50f00f81238be13a5229a6226a947176ab879eba46049ef36306b651"
    },
    {
      "frame_id": "R058",
      "source_ordinal": 1887,
      "global_seconds_exact": "629629/10000",
      "window_local_seconds_exact": "29629/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R058_O001887.png",
