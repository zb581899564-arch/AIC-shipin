已完成独立新代码接口，全部位于 `improvement/local_boundary_v1`；未修改任何冻结旧代码，未部署、未执行任何script、下载、CPU准备、GPU/训练、独立重放或封包。

本次只读核实了原 `runtime.encode`、`baseline_frames`、`tensor_signature`、旧CPU native64准备、GPU journal/grammar与独立CPU重放接口，以及Linux主机身份/现有资源。旧四条外部pipeline的媒体、完整clock、RGB、processor、真实模型和重放继续复用，不重做。

实现文件：`lb_contract.py`、`lb_grammar.py`、`lb_io.py`、`plan_local_inputs.py`、`prepare_local_inputs.py`、`infer_local_boundaries.py`、`replay_local_boundaries.py`、`README.md`。

静态内容检查：

- 原case/segment/window局部秒与全源归一秒精确转换，注册端点必须与原B done一致。
- 原源SHA/clock/CPU proof/request/raw/done/replay/source isolation互绑；只允许既有四个外部非测试root进入。
- 新输入64不同帧，短窗±3s，不放宽帧门、不拉伸标签、不调FPS、不隐藏截断。
- 真实actual grid/pixels/input token来自原processor证据；未把131072声明为实际每帧像素。
- finite KEEP/UNKNOWN/REFINE，start按首纳帧PTS，end按末纳帧下一native PTS/实测正duration。
- 相邻duration不足、不连续、缺外侧或edge index明确UNKNOWN保留；模型/绑定/grammar failure阻断，无空事件回退。
- GPU读取已验收的CPU tensor文件，依原runtime tensor signature核CPU/GPU一致，完整唯一request journal保留raw。
- 新独立CPU重放不加载模型；原生转换使用独立实现，完整实际模型终态与共享ledger一致后才执行。
- 起止交叉保留原点并显式登记，无端点交换、无删除事件。

这些是代码设计/静态读回结果，尚未确认Linux语法、真实PyAV duration可用性、实际processor token预算、模型新schema行为或科学收益。主代理需冻结protocol后部署并做最小语法/合成检查，再决定是否执行新CPU门。重复阶段及失败恢复均需新明确登记，成功产物不重跑。

批判代理一次讨论已并入同候选内侧锚点/方向、镜头切换风险、edge/UNKNOWN、位移及核心/非事件泄漏诊断。规则小回执由critic独立当前读取；接口只绑定回执，不将规则解读升级为官方许可。
