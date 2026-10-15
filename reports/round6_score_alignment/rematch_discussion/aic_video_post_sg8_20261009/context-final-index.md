# 完整连续分卷索引

任务 AIC-VIDEO-REMATCH-NEXT-20261005。必须按序完整读取以下所有分卷，不能只读最后一卷。分卷原字节顺序拼接即完整原包，无删减、无摘要替代；代码围栏可能跨卷，请按连续文本读取。继承旧轮次的阶段/额度只为历史，当前事实和主控新问题位于最后卷。请明确每卷实际读取范围与截断，缺卷不得宣称全读。

```json
{
  "packet": "context-final.md",
  "bytes": 793724,
  "sha256": "e86ccd6489ba2a0790c09ca49515be87b0131430ad8aeb15413e605b871d017d",
  "parts": [
    {
      "file": "context-final-part01.md",
      "bytes": 139971,
      "sha256": "5a384064cda6c480a626fe94f3dab13ea860eacc20f244482dc5711b9116fb3d",
      "byte_start": 0,
      "byte_end_exclusive": 139971,
      "first_line": 1,
      "last_line": 2066
    },
    {
      "file": "context-final-part02.md",
      "bytes": 139765,
      "sha256": "5d7ef1084e41047512cebd3dc763e610fbc83ee26794756f6ebff3cb495befba",
      "byte_start": 139971,
      "byte_end_exclusive": 279736,
      "first_line": 2067,
      "last_line": 3990
    },
    {
      "file": "context-final-part03.md",
      "bytes": 139980,
      "sha256": "1428a68eb5e19e230759406a2a1297074b346b7d476828ae544f9a6a719aa5fc",
      "byte_start": 279736,
      "byte_end_exclusive": 419716,
      "first_line": 3991,
      "last_line": 5873
    },
    {
      "file": "context-final-part04.md",
      "bytes": 139996,
      "sha256": "7a218787472180dd6824cb21f92ee545e2ca7d87592d3032b47ade9c00c8d17c",
      "byte_start": 419716,
      "byte_end_exclusive": 559712,
      "first_line": 5874,
      "last_line": 8429
    },
    {
      "file": "context-final-part05.md",
      "bytes": 139933,
      "sha256": "7bc7a24422aa8ae514df203b803fd55953b4592061586914330b27f2dfbd17a7",
      "byte_start": 559712,
      "byte_end_exclusive": 699645,
      "first_line": 8430,
      "last_line": 10603
    },
    {
      "file": "context-final-part06.md",
      "bytes": 94079,
      "sha256": "27f08166fe271823786cf701054efa535b0940ef9de268f794afc73f9307195b",
      "byte_start": 699645,
      "byte_end_exclusive": 793724,
      "first_line": 10604,
      "last_line": 11949
    }
  ],
  "exact_concatenation": true,
  "no_content_omitted": true
}
```
