#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
cd "$R/src" || exit 1
rm -f "$R/evidence/OraRL_src.tar.gz"
tar czf "$R/evidence/OraRL_src.tar.gz" --exclude=.git OraRL
ls -la "$R/evidence/OraRL_src.tar.gz"
sha256sum "$R/evidence/OraRL_src.tar.gz"
echo
echo '=== copy small model configs into evidence ==='
for f in config.json processor_config.json generation_config.json tokenizer_config.json chat_template.jinja README.md model.safetensors.index.json; do
  if [ -f "$R/model/Video-ORA-4B/$f" ]; then
    cp "$R/model/Video-ORA-4B/$f" "$R/evidence/model_$f"
    echo "copied $f"
  else
    echo "MISSING $f"
  fi
done
echo
echo '=== download progress ==='
du -sh "$R/model/Video-ORA-4B"
ls -la "$R/model/Video-ORA-4B"/*.safetensors 2>&1 | head
