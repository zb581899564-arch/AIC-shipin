import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = (HERE / "before/budget_run.py").read_text(encoding="utf-8")
helper = '''
def load_resource_policy(path):
    """Missing policy preserves the historical cap; unlimited must be explicit."""
    if not path.exists():
        return dict(gpu_time_mode='FINITE', max_total_gpu_seconds=86400,
                    policy_sha256=None, policy_source='legacy_default')
    raw = path.read_bytes()
    policy = json.loads(raw)
    if not isinstance(policy, dict) or policy.get('schema_version') != 1:
        raise ValueError('invalid resource policy schema')
    if 'max_total_gpu_seconds' not in policy:
        raise ValueError('missing cumulative GPU limit')
    mode = policy.get('gpu_time_mode')
    cap = policy['max_total_gpu_seconds']
    if mode == 'UNLIMITED':
        if cap is not None:
            raise ValueError('unlimited policy requires a null limit')
    elif mode == 'FINITE':
        if type(cap) is not int or cap <= 0:
            raise ValueError('finite policy requires a positive integer limit')
    else:
        raise ValueError('unknown GPU time mode')
    return dict(gpu_time_mode=mode, max_total_gpu_seconds=cap,
                policy_sha256=hashlib.sha256(raw).hexdigest(),
                policy_source=str(path))


def check_gpu_reservation(charged, max_seconds, teardown_reserve, policy):
    if type(max_seconds) is not int or max_seconds <= 0:
        raise ValueError('invalid job wall time')
    cap = policy['max_total_gpu_seconds']
    if cap is not None and charged + max_seconds + teardown_reserve > cap:
        raise RuntimeError(
            f'GPU reservation exceeds budget: {charged}+{max_seconds}+{teardown_reserve}>{cap}')


'''
assert source.count("import json\n") == 1
source = source.replace("import json\n", "import json\nimport hashlib\n")
assert source.count("def main():\n") == 1
source = source.replace("def main():\n", helper + "def main():\n")
old = """    if charged + args.max_seconds + teardown_reserve > 86400:
        raise RuntimeError(f'GPU reservation exceeds budget: {charged}+{args.max_seconds}+{teardown_reserve}>86400')
"""
new = """    policy = load_resource_policy(ROOT / 'resource_policy.json')
    check_gpu_reservation(charged, args.max_seconds, teardown_reserve, policy)
"""
assert source.count(old) == 1
source = source.replace(old, new)
old_record = "prior_charged_seconds=charged, disk_before=before)"
new_record = """prior_charged_seconds=charged, disk_before=before,
                  gpu_time_mode=policy['gpu_time_mode'],
                  max_total_gpu_seconds=policy['max_total_gpu_seconds'],
                  resource_policy_sha256=policy['policy_sha256'])"""
assert source.count(old_record) == 1
source = source.replace(old_record, new_record)
(HERE / "budget_run.py").write_text(source, encoding="utf-8")
policy = dict(schema_version=1, gpu_time_mode="UNLIMITED",
              max_total_gpu_seconds=None,
              authorized_by="user", authorized_at_utc="2026-10-05T07:57:35Z",
              authorization_text="GPU预算时间调整为无限制",
              scope="/home/inspur/aic_video_work",
              ledger_initial_charge_seconds=7200,
              added_disk_budget_gib=80,
              preserve_frozen_experiment_protocols=True,
              preserve_shared_gpu_exclusivity=True,
              policy_run_id=HERE.name)
(HERE / "resource_policy.json").write_text(
    json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(original_sha256=hashlib.sha256(
    (HERE / "before/budget_run.py").read_bytes()).hexdigest(),
    revised_sha256=hashlib.sha256((HERE / "budget_run.py").read_bytes()).hexdigest())))
