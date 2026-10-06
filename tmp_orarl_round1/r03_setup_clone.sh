#!/usr/bin/env bash
set -u
ROUND=/home/inspur/aic_video_work/orarl_round1
mkdir -p "$ROUND"/{logs,scripts,src,model,outputs,evidence}

echo "=== HF MODEL FILE LIST (official, via hf-mirror) ==="
curl -sS --max-time 60 "https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true" \
  -o "$ROUND/evidence/hf_model_api.json"
python3 - <<'PY'
import json
p='/home/inspur/aic_video_work/orarl_round1/evidence/hf_model_api.json'
d=json.load(open(p))
print('modelId :', d['modelId'])
print('sha     :', d['sha'])
print('lastMod :', d.get('lastModified'))
sibs=d.get('siblings',[])
print('file count:', len(sibs))
tot=0
for s in sorted(sibs, key=lambda x: x['rfilename']):
    sz=s.get('size')
    tot += sz or 0
    print('  %-45s %s' % (s['rfilename'], sz))
print('total bytes: %d (%.2f GiB)' % (tot, tot/2**30))
PY

echo
echo "=== GIT CLONE VIA MIRROR ==="
cd "$ROUND/src" || exit 1
if [ -d OraRL/.git ]; then
  echo "already present, fetching instead"
  git -C OraRL fetch --all --tags
else
  rm -rf OraRL.partial
  git clone --progress https://ghproxy.net/https://github.com/HVision-NKU/OraRL.git OraRL.partial 2>&1 | tail -20
  if [ -d OraRL.partial/.git ]; then mv OraRL.partial OraRL; fi
fi
echo "-- result --"
ls -la "$ROUND/src" 2>&1
if [ -d OraRL/.git ]; then
  echo "HEAD: $(git -C OraRL rev-parse HEAD)"
  echo "remote:"; git -C OraRL remote -v
  echo "-- log --"; git -C OraRL log --oneline -5
  echo "-- commit e1ec91ff present? --"
  git -C OraRL cat-file -t e1ec91ff00f59ee0da04d285938c1f7247daa69c 2>&1
  echo "-- tree --"; ls -la OraRL
else
  echo "CLONE FAILED"
fi
