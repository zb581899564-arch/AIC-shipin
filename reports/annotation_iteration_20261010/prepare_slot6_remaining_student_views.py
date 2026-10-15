"""The same accepted CPU export algorithm for the twenty untouched plan windows."""
from pathlib import Path
base=Path(__file__).resolve().parent/'prepare_slot6_student_views.py'
code=base.read_text(encoding='utf-8')
changes={
    "['first_four']":"['jobs'][4:]",
    "'student_views_cpu_receipt.json'":"'remaining_student_views_cpu_receipt.json'",
    "'student_views_cpu_failure_01.json'":"'remaining_student_views_cpu_failure_01.json'",
    "'PASS_FOUR_ACTUAL_CPU_STUDENT_VIEW_EXPORTS'":"'PASS_TWENTY_REMAINING_ACTUAL_CPU_STUDENT_VIEW_EXPORTS'",
    "runtime_sha256=sha(RUN/'context_advisory_v1/runtime.py')":"export_code_sha256=sha(base), runtime_sha256=sha(RUN/'context_advisory_v1/runtime.py')",
}
for old,new in changes.items():
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),dict(__file__=str(base),__name__='__main__',base=base))
