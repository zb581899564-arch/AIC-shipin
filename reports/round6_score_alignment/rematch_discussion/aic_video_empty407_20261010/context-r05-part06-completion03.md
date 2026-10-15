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
