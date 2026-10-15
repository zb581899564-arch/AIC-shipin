"""Read-only current workflow gate. Never import or execute a legacy runner."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path(__file__).with_name('policy.json')


def decide(policy, backend, entrypoint=None):
    if backend == 'closed-agent':
        return 'DENY_RETIRED_CLOSED_AGENT_ANNOTATION'
    if entrypoint is not None:
        path = Path(entrypoint)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        for relative in policy['retired_roots']:
            retired = (ROOT / relative).resolve()
            if path == retired or retired in path.parents:
                return 'DENY_RETIRED_HISTORICAL_ENTRYPOINT'
    if policy['state'] == 'NO_ACTIVE_ANNOTATION':
        return 'DENY_NO_ACTIVE_BULK_ANNOTATION'
    if policy['state'] != 'READY' or policy['execution_authorized'] is not True:
        return 'DENY_ANALYSIS_ONLY_NO_EXPERIMENT_AUTHORIZATION'
    # An approved future implementation needs a separately reviewed launcher.
    # Editing a policy bit alone must not start code, models, or subprocesses.
    return 'DENY_NO_REVIEWED_EXECUTION_IMPLEMENTATION'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('status', 'check', 'run'))
    parser.add_argument('--backend', choices=('local-direct', 'closed-agent'),
                        default='local-direct')
    parser.add_argument('--entrypoint')
    args = parser.parse_args()
    policy = json.loads(POLICY.read_text(encoding='utf-8-sig'))
    if args.action == 'status':
        print(json.dumps({
            'state': policy['state'],
            'active_experiment': policy['active_experiment'],
            'closed_agent_annotation': policy['closed_agent_annotation'],
            'execution_authorized': policy['execution_authorized'],
            'diagnostic_experiments': policy.get('diagnostic_experiments', {}),
            'risk_submission_iterations': policy.get('risk_submission_iterations', {}),
            'model_calls': 0, 'subprocesses_started': 0,
        }, ensure_ascii=False))
        return 0
    reason = decide(policy, args.backend, args.entrypoint)
    print(json.dumps({'status': reason, 'model_calls': 0,
                      'subprocesses_started': 0, 'training_started': False},
                     ensure_ascii=False))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
