#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round2
W=/home/inspur/aic_video_work
RID="$1"; MAXW="${2:-600}"
J="$W/improvement_round1/$RID.log"
DEADLINE=$(( $(date +%s) + MAXW ))
while :; do
  if [ -f "$W/improvement_round1/$RID.resource.json" ]; then echo "SETTLED"; break; fi
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then echo "POLL_TIMEOUT"; break; fi
  sleep 15
done
echo
echo "=== $RID log (grep) ==="
grep -vE '^\s*[0-9]+%\|' "$J" 2>/dev/null | tail -40
echo
echo "=== resource ==="
python3 -c "
import json
d=json.load(open('$W/improvement_round1/$RID.resource.json'))
print('name=%s charged=%.1fs status=%s exit=%s peak=%s stop=%s' % (d['name'], d['charged_seconds'], d['status'], d.get('exit_code'), d.get('sampled_peak_memory_mib'), d.get('stop_reason')))
" 2>&1
echo
echo "=== per-case status ==="
python3 - <<PY
import json, pathlib
p = pathlib.Path("$R/outputs/$RID/run_status.json")
if p.exists():
    st = json.loads(p.read_text())
    print("exit_code:", st["run"].get("exit_code"), " n_failed:", st["run"].get("n_failed"))
    for c in st["cases"]:
        print("  %-22s %-20s parseable=%-5s protocol=%-5s success=%-5s quality=%s" % (
            c["case_id"], c["task"], c["output_parseable"], c["protocol_complete"],
            c["task_success"], c["quality"]["status"]))
        if c.get("parse_errors"):
            print("      errors:", c["parse_errors"][:2])
else:
    print("no run_status.json")
PY
