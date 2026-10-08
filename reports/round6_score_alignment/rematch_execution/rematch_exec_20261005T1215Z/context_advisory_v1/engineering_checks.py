"""CPU checks of actual downstream gates and immutable module bindings."""
import json
from pathlib import Path
import context_contract as cc
import runtime as rt
import experiment as ex


def main():
    report = rt.load(rt.HERE / "report.py", "cad_report_cpu")
    cases = [
        ((True, 0., 0., [0.,0.,0.,0.]), (False,False,True)),
        ((False, -.05, .75, [-.05,0.,0.,0.]), (False,True,False)),
        ((False, 0., 0., [0.,0.,0.,0.]), (True,False,True)),
        ((False, .1, 0., [.1,.1,-.001,.1]), (False,False,False)),
        ((False, .1, 0., [.1,.1,.1,.1]), (True,False,True))]
    for args, expected in cases:
        cc.require(report.investment_decision(*args) == expected, "registered investment gate changed")
    # Unbalanced source groups: the point estimate must be video-macro, not
    # a group mean masquerading as the matching bootstrap estimand.
    result = report.bootstrap_video_macro([1.,1.,0.], [dict(source_group='a'),dict(source_group='a'),dict(source_group='b')], draws=100)
    cc.require(result["mean"] == 2/3 and result["resampling_units"] == 2, "wrong bootstrap estimand")
    student, old, _, production = rt.bind_helpers()
    import inspect
    import engine
    cc.require(Path(engine.__file__).resolve() == (rt.RUN / "teacher_student_autopilot_v14/precision_helpers/engine.py").resolve(), "wrong real model engine")
    cc.require(str(inspect.signature(engine.load_model)) == '(config, adapter=True)', "actual engine interface changed")
    pack = rt.load(rt.HERE / "packager.py", "cad_package_cpu")
    final = rt.load(rt.HERE / "final_acceptance.py", "cad_final_cpu")
    fallback = rt.load(rt.HERE / "fallback.py", "cad_fallback_cpu")
    cc.require(callable(pack.assemble) and callable(pack.finish) and callable(final.main) and callable(fallback.inventory), "downstream modules not loadable")
    draft = ex.read(rt.HERE / "draft_preflight.json")
    cc.require(draft["status"] == "PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS" and len(draft["non_test_proofs"]) == 8, "actual prior CPU processor proof missing")
    bindings = {str(rt.HERE/p): ex.sha(rt.HERE/p) for p in ('context_contract.py','runtime.py','experiment.py','tests.py')}
    cc.require(all(Path(p).stat().st_mtime_ns <= (rt.HERE/'draft_preflight.json').stat().st_mtime_ns for p in bindings),
        'processor code was modified after actual CPU proof; rerun is required')
    rt.raw_write(rt.HERE / "cpu_build_acceptance.json", {"status":"PASS_CPU_ENGINEERING_GATES_AND_ACTUAL_MODULE_BINDING", "investment_cases":5,
        "bootstrap_unbalanced_group_case":True, "actual_bound_model_engine":engine.__file__,
        "processor_code_bindings":bindings, "actual_original_processor_proof_sha256":ex.sha(rt.HERE/'draft_preflight.json'),
        "processor_proof_reused_no_new_processor_calls":True, "new_model_calls":0,"optimizer_updates":0})
    print("PASS_CPU_ENGINEERING_GATES_AND_ACTUAL_MODULE_BINDING", flush=True)


if __name__ == '__main__':
    main()
