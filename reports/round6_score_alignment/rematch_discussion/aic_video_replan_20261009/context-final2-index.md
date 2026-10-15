# 完整连续分卷索引

任务 AIC-VIDEO-REMATCH-NEXT-20261005。必须按序完整读取以下所有分卷，不能只读最后一卷。分卷原字节顺序拼接即完整原包，无删减、无摘要替代；代码围栏可能跨卷，请按连续文本读取。继承旧轮次的阶段/额度只为历史，当前事实和主控新问题位于最后卷。请明确每卷实际读取范围与截断，缺卷不得宣称全读。

```json
{
  "packet": "context-final2.md",
  "bytes": 631777,
  "sha256": "442036c60c2fe2a48b050679acbd41f7e1d80ee879e14f4810107a5cb64c0c7c",
  "parts": [
    {
      "file": "context-final2-part01.md",
      "bytes": 139971,
      "sha256": "5a384064cda6c480a626fe94f3dab13ea860eacc20f244482dc5711b9116fb3d",
      "byte_start": 0,
      "byte_end_exclusive": 139971,
      "first_line": 1,
      "last_line": 2066
    },
    {
      "file": "context-final2-part02.md",
      "bytes": 139765,
      "sha256": "5d7ef1084e41047512cebd3dc763e610fbc83ee26794756f6ebff3cb495befba",
      "byte_start": 139971,
      "byte_end_exclusive": 279736,
      "first_line": 2067,
      "last_line": 3990
    },
    {
      "file": "context-final2-part03.md",
      "bytes": 139980,
      "sha256": "1428a68eb5e19e230759406a2a1297074b346b7d476828ae544f9a6a719aa5fc",
      "byte_start": 279736,
      "byte_end_exclusive": 419716,
      "first_line": 3991,
      "last_line": 5873
    },
    {
      "file": "context-final2-part04.md",
      "bytes": 139996,
      "sha256": "7a218787472180dd6824cb21f92ee545e2ca7d87592d3032b47ade9c00c8d17c",
      "byte_start": 419716,
      "byte_end_exclusive": 559712,
      "first_line": 5874,
      "last_line": 8429
    },
    {
      "file": "context-final2-part05.md",
      "bytes": 72065,
      "sha256": "6176f6a23e14e0f209a93bbd563c137847093d4f43f5b463d942b792e3e96471",
      "byte_start": 559712,
      "byte_end_exclusive": 631777,
      "first_line": 8430,
      "last_line": 9614
    }
  ],
  "exact_concatenation": true,
  "no_content_omitted": true
}
```
