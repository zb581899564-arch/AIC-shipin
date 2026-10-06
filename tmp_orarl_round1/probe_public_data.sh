#!/usr/bin/env bash
# Timeboxed probe for legally-obtainable, publicly-trusted grounding data.
set -u
echo "=== can we reach candidate public data hosts? ==="
probe() { curl -sS -o /dev/null -w "$1 http=%{http_code} t=%{time_total}\n" --max-time 15 "$2" 2>&1; }
probe "hf-mirror api           " https://hf-mirror.com/api/datasets?search=refcoco
probe "hf-mirror datasets-srv  " https://datasets-server.huggingface.co/
probe "huggingface datasets-srv" https://datasets-server.huggingface.co/
probe "cocodataset.org         " http://images.cocodataset.org/
probe "raw.githubusercontent   " https://raw.githubusercontent.com/
probe "objects.githubusercontent" https://objects.githubusercontent.com/
probe "github.com              " https://github.com/
probe "openimages              " https://storage.googleapis.com/openimages/web/index.html
probe "visualgenome            " https://visualgenome.org/
echo
echo "=== hf-mirror dataset search (refcoco) ==="
curl -sS --max-time 25 "https://hf-mirror.com/api/datasets?search=refcoco&limit=25" 2>&1 \
  | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for x in d: print('  %-55s downloads=%s likes=%s' % (x.get('id'), x.get('downloads'), x.get('likes')))
except Exception as e: print('parse fail', e)
"
echo
echo "=== hf-mirror dataset search (grounding / coco small) ==="
curl -sS --max-time 25 "https://hf-mirror.com/api/datasets?search=refcoco%2B&limit=15" 2>&1 \
  | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for x in d: print('  %-55s downloads=%s' % (x.get('id'), x.get('downloads')))
except Exception as e: print('parse fail', e)
"
echo
echo "=== does huggingface_hub reach the mirror from the orarl env? ==="
export HF_ENDPOINT=https://hf-mirror.com
/home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python - <<'PY'
import os
print("HF_ENDPOINT =", os.environ.get("HF_ENDPOINT"))
try:
    from huggingface_hub import HfApi
    api = HfApi(endpoint=os.environ["HF_ENDPOINT"])
    ds = api.list_datasets(search="refcoco", limit=12)
    for d in ds:
        print("  ", d.id, getattr(d, "downloads", None))
except Exception as e:
    print("  hub API failed:", type(e).__name__, str(e)[:200])
PY
