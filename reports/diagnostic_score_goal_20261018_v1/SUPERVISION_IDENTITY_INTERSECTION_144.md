# TIME训练来源与正式426的已知身份交集：144

2026-10-18。本项是新的manifest身份比对用途，未重做旧pilot审计。只访问现存manifest的字段名及ID/path/SHA字符串；不查看target值、测试媒体/GT，不运行模型/processor，不扫描媒体哈希，不下载。机器证据见同目录 `SUPERVISION_IDENTITY_INTERSECTION_144.json`。

**结果：TIME的704个原媒体SHA与当前正式426的425个不同媒体SHA，已知精确字节交集为0；原YouTube/拍摄来源交集仍为UNKNOWN。** 同文件不同编码、窗口、裁切、转载和相同原事件均不在本项可证明范围。

## 本地绑定与结果

- 训练registry：`reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1/inputs_01/r7_train_registry.json`，SHA `71552f64ccdb125ca11a451baf5b8a22491d51d73db1a42e0ce1a545262d1cd4`。704父记录，704个不同 `source_sha256`、704条 `source_path`、602个 `youtube_id`。
- 训练窗口：同目录 `full_train.jsonl`，SHA `124801624736f960d15074ad65840d4e2850dcb7d8d5d3b16a2cb54e7eee4bc0`。724窗口覆盖全部704父ID，父ID越出registry为0，窗口的source path/SHA/YouTube-ID三元组与registry不匹配为0。没有读取 `segments_clip_local` 等目标值。
- 正式缓存：`controller/pts_v4_scan_01/clean_manifest_v2.json`，SHA `ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8`。路径均以上述 `rematch_exec_20261005T1215Z` 为根。其426条记录有426个video_id、425个不同媒体SHA。
- 另核同根 `controller/m0_finalize_01/clean_manifest_426.json` 与 `b_sft8b_package_v3/delivery_01/metadata.json`，三份426的video_id/SHA集合完全相等。
- 对三份正式缓存分别比对：与TIME704的原媒体SHA交集均为 **0**，source_path字面交集均为 **0**。不将数字官方ID与训练编号硬匹配。

## 当前40.47身份绑定

主代理本轮经既有home严格SSH仅只读metadata，确认主机 `inspur-NP5570M5`；当前生产 `/home/inspur/aic_video_work/semantic_context_production_20261016_v1/metadata.json` 文件SHA为 `c3612851513f83b2ea1968f3149bf64fbdd57a6d654370ecb31f15c817768936`、426条。

主代理与本地采用同一独立身份canonical配方：

```python
pairs = [[str(r['video_id']), r['source_sha256']] for r in records]
pairs.sort(key=lambda x: int(x[0]))
sha256(json.dumps(pairs, separators=(',', ':'), ensure_ascii=True).encode('utf-8'))
```

旧pts426和本轮当前426均为 `b714743ce224aff344fd679c302506bf758d9c444ba34a74e1a6e3a76a8f1328`，故本地精确SHA交集0可绑定到当前426身份集合。此处只采用主代理回传的metadata摘要，没有回传完整正式metadata或打开媒体。绝对路径与主代理摘要已记录于144 JSON的 `current_formal_binding`，补证没有重新计算交集。路径交集0是旧426映射manifest中的字面结果；当前路径字段未回传，不把ID/SHA相等外推为当前路径逐字相等。

注意：144 JSON早先的 `video_id_sha256_identity_set_sha256` 使用字符串ID排序，是另一明确recipe；它不能与上述数字ID排序的canonical直接互换。

## UNKNOWN与结论限制

- 正式缓存没有 `youtube_id`，文件名为数字、source_group为 `rematch:ID`。主代理也确认当前metadata首条没有YouTube/original字段。因此**无法用这些材料计算原YouTube ID或更早原素材的交集**；该项记UNKNOWN，不记0。
- 路径分离与SHA不相等不证明全局来源隔离，也不解决987原分享发布者/许可的UNKNOWN。反过来，即便未来发现共享YouTube ID，也应核具体媒体、窗口、用途与规则，不单靠同ID宣称违规。
- 本项仅减少143中“当前TIME704媒体是否与正式426逐字节相同”的不确定性，不形成训练/生产新准入、不改变任何旧STOP。已完成所需最小比对，停止探索。
