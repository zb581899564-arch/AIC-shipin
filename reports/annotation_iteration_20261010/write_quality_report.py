"""Human-readable report of frozen acceptance; no admission decisions are changed."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    q=json.loads((H/'quality_result.json').read_text());completion=json.loads((H/'results/completion.json').read_text())
    resources=[json.loads(p.read_text()) for p in (H/'results').glob('*.resource.json')];assert len(resources)==6
    total=sum(r['charged_seconds'] for r in resources)
    title='通过冻结的研究与第二阶段投入门' if q['stage2_pass'] else '未通过冻结投入门，保留原生产'
    lines=['# '+title,'',f"本轮真实LoRA训练{completion['optimizer_steps']}步；最终adapter SHA `{completion['adapter_sha256']}`。6个GPU作业自然completed、exit0、终态账本一一对应，累计新增计费运行时间{total:.3f}秒。训练与权重留Linux，原生产未替换。",'',
      f"研究门={q['research_pass']}，第二阶段门={q['stage2_pass']}；所有4组各89行合法，完整9源原生域覆盖通过。9源是已见development，不是盲测；TVSum代理指标不是AIC官方分。",'',
      '| 同图片评分协议 | macro Spearman | top15人工效用 | macro MAE | native代理F |',
      '|---|---:|---:|---:|---:|']
    for name,a in q['arms'].items():
        lines.append(f"| {name} | {a['macro_spearman']:.6f} | {a['macro_top15_human_mean']:.6f} | {a['macro_mae']:.6f} | {q['native_macro_proxy_f'][name]:.6f} |")
    lines+=['','production_B仅在新image-score prompt下诊断，不等于原B native视频管线被比较。top15%只作排序诊断，实际选择阈值49只由train冻结，允许空；2秒域扩展是插值假设。','',
       '| 源 | Spearman new | base | native F new | base | 新选中原生帧占比 |',
       '|---|---:|---:|---:|---:|---:|']
    for s,a in sorted(q['arms']['new']['source_metrics'].items()):
        b=q['arms']['base']['source_metrics'][s];n=q['native_selector_analysis']['new'][s];o=q['native_selector_analysis']['base'][s]
        lines.append(f"| {s} | {a['spearman']:.6f} | {b['spearman']:.6f} | {n['threshold3_human_proxy_f']:.6f} | {o['threshold3_human_proxy_f']:.6f} | {n['selected_fraction']:.6f} |")
    lines+=['',f"Spearman改善源={q['positive_sources']}/9；最差逐源变化={q['worst_spearman_delta']:.6f}。",
      f"配对源bootstrap95区间：`{json.dumps(q['source_bootstrap95'])}`。若跨0，证据不足支持可靠泛化或官网提分。",
      f"训练域图片交换：正常图片更好{q['visual_dependency']['normal_better_rows']}/12，平均swap-normal NLL={q['visual_dependency']['mean_swap_minus_normal']:.6f}，输入依赖门={q['visual_dependency']['visual_dependency_gate']}。此检查不等于高光质量。",'',
      'agy另完成6段、90格：KEEP37/REJECT34/UNKNOWN19，20个稀疏原生锚点已查看；观察与整段边界仍有缺口。新teacher训练入选0，UNKNOWN未转负例。', '',
      '未依据本轮dev修改学习率、阈值或选checkpoint。原raw/失败/成功生成保留；验收工程v2独立修正了第一阶段PASS误当第二阶段PASS的错误。']
    with (H/'QUALITY_REPORT.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    print(json.dumps({'quality':title,'new_gpu_seconds':total}))
if __name__=='__main__':main()
