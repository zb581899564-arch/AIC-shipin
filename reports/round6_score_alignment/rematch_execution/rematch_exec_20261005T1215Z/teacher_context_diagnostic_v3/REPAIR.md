# 独立v2：帧证据配对与时间表示合同

v1于2026-10-08 00:25:00 UTC+8停止，0/4合格请求、T更新0。原raw、HTTP、真实processor/runtime grammar和STOP全部保存，不重开v1、不修改或复用失败回答。

真实回答frame_ordinal1723对应的native窗口内PTS为11.86345833333333，模型写12.36395833333333，差0.5005秒。v1将ordinal与时间分别限定enum，实际grammar允许交叉配对；独立validator已正确拒绝，不能调大容差或自动纠正此回答。另已实际复现固定C++ JSON/runtime将numeric const的13.782041666666667变成grammar里的13.782041666666666，原始十进制身份有差异，应一并消除表示冲突。最初CPU测试把差异猜成15位截取，该预期错误已在冻结前纠正；保留旧CPU错误回执与源文件，不将猜测当事实。

v2的evidence items为每个实际帧{ordinal const, decimal-string time const}的完整anyOf，绑定二者。区间端点也是原采样端点/0/窗口末端的十进制字符串enum，保持原数据的完整数值身份；运行验证用Decimal精确比较，不截段/round/降低门。此诊断不生成学生标签，未修改原validator或任何旧标签数字。

两条window选择、目标64帧、整段64 overview、权重、源片、高光定义、配对arm和四次确定性请求均沿用原预登记；只独立登记输出表示/帧时间配对修复。原失败回答在新grammar与validator必须被拒绝；全部128真实采样端点在实际固定runtime grammar必须可表达且错误ordinal/time组合不可表达。CPU先复现两类旧问题，再验修复；绑定独立source_lock后共享wrapper单次启动。
