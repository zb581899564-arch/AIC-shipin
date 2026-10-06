#!/usr/bin/env bash
# Build the fixed, reproducible sample set for this round.
#
# Samples are DERIVED from read-only project source videos. Task INPUTS
# (the spatial expression, the temporal event phrase, the tracking target
# description) are defined for this demonstration and are NOT human ground
# truth. Nothing here uses the AIC test set.
#
# Clip length is 32 s on purpose: the author's tracking profile is
# TRACKING_FPS=1 / TRACKING_MAX_FRAMES=32, i.e. a task bounded at 32 seconds.
# With a longer clip, max_frames=32 would spread the 32 samples over the whole
# clip and "second N" would no longer sit near N seconds.
set -u
R=/home/inspur/aic_video_work/orarl_round1
FFMPEG=/usr/local/bin/ffmpeg
FFPROBE=/home/inspur/anaconda3/envs/Andy/bin/ffprobe
SRC=/home/inspur/aic_video_data/videos/w/wk2CeU_DcBo_60.0_210.0.mp4
LEN=32

mkdir -p "$R/clips" "$R/frames" "$R/evidence"
CLIP="$R/clips/src_wk2CeU_DcBo_60_210_off0_len32.mp4"
FRAME="$R/frames/sg_frame_off0.png"

echo "=== SOURCE ==="
echo "path: $SRC"
"$FFPROBE" -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,codec_name \
  -show_entries format=duration,size,format_name,bit_rate \
  -of json "$SRC"
sha256sum "$SRC"

echo
echo "=== BUILD ${LEN}s DERIVED CLIP (offset 0.0, stream copy, no re-encode) ==="
"$FFMPEG" -nostdin -y -v error -ss 0 -i "$SRC" -t "$LEN" -c copy \
  -avoid_negative_ts make_zero "$CLIP"
echo "clip: $CLIP"
"$FFPROBE" -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,nb_frames,codec_name \
  -show_entries format=duration,size -of json "$CLIP"
sha256sum "$CLIP"

echo
echo "=== EXTRACT SPATIAL-GROUNDING STILL (t=0, lossless PNG) ==="
"$FFMPEG" -nostdin -y -v error -ss 0 -i "$SRC" -frames:v 1 "$FRAME"
echo "frame: $FRAME"
"$FFPROBE" -v error -select_streams v:0 -show_entries stream=width,height -of json "$FRAME"
sha256sum "$FRAME"

echo
echo "=== SAMPLE MANIFEST ==="
python3 - <<'PY'
import hashlib, json, subprocess
R = '/home/inspur/aic_video_work/orarl_round1'
FFPROBE = '/home/inspur/anaconda3/envs/Andy/bin/ffprobe'
SRC = '/home/inspur/aic_video_data/videos/w/wk2CeU_DcBo_60.0_210.0.mp4'
CLIP = f'{R}/clips/src_wk2CeU_DcBo_60_210_off0_len32.mp4'
FRAME = f'{R}/frames/sg_frame_off0.png'

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def probe(p):
    out = subprocess.check_output([FFPROBE, '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,codec_name',
        '-show_entries', 'format=duration,size,format_name', '-of', 'json', p], text=True)
    return json.loads(out)

def frac(s):
    if not s: return None
    if '/' in s:
        n, d = s.split('/');  return float(n) / float(d) if float(d) else None
    return float(s)

src, clip, fr = probe(SRC), probe(CLIP), probe(FRAME)
s, c, f = src['streams'][0], clip['streams'][0], fr['streams'][0]
clip_dur = float(clip['format']['duration'])
clip_fps = frac(c.get('avg_frame_rate'))
clip_n = int(c['nb_frames']) if c.get('nb_frames') else None

manifest = {
  'round': 'orarl_round1',
  'generated_utc': subprocess.check_output(['date','-u','+%FT%TZ'], text=True).strip(),
  'trust_statement': ('Task INPUTS below are defined for this demonstration. They are NOT human '
                      'ground truth. No AIC test video, frame, or label is used. Results from this '
                      'sample set prove the pipeline runs; they are diagnostic only and must not be '
                      'reported as accuracy.'),
  'source': {
    'path': SRC, 'sha256': sha(SRC),
    'width': s['width'], 'height': s['height'],
    'fps_avg': frac(s.get('avg_frame_rate')), 'fps_r': frac(s.get('r_frame_rate')),
    'nb_frames': int(s['nb_frames']) if s.get('nb_frames') else None,
    'duration_sec': float(src['format']['duration']),
    'codec': s['codec_name'], 'size_bytes': int(src['format']['size']),
    'partition': '/home/inspur/aic_video_data/videos (project source pool, read-only)',
  },
  'derived_clip': {
    'path': CLIP, 'sha256': sha(CLIP),
    'source_offset_sec': 0.0, 'requested_length_sec': 32.0,
    'method': 'ffmpeg -ss 0 -t 32 -c copy (stream copy, no re-encode)',
    'width': c['width'], 'height': c['height'],
    'fps_avg': clip_fps,
    'nb_frames': clip_n,
    'duration_sec': clip_dur,
    'time_mapping': ('t_source = t_clip + 0.0 ; frame_index_source = frame_index_clip '
                     '(offset is zero, so clip time == source time within the clip)'),
  },
  'derived_frame': {
    'path': FRAME, 'sha256': sha(FRAME),
    'source_offset_sec': 0.0,
    'method': 'ffmpeg -ss 0 -frames:v 1 (lossless PNG)',
    'width': f['width'], 'height': f['height'],
  },
  'tasks': {
    'spatial_grounding_image': {
      'input_image': FRAME,
      'expression': 'the man in the white sleeveless shirt',
      'prior_required': 'natural-language referring expression (author RefCOCO protocol)',
      'ground_truth': None,
      'note': 'expression written by the executing agent after viewing the frame',
    },
    'temporal_grounding_video': {
      'input_video': CLIP,
      'event': 'Man and woman walk through the park sidewalk together.',
      'event_source': ('frozen_data/dev.jsonl row qvh_934 query field '
                       '(trusted_identity=false, source_trust_status=PENDING_SUPERVISOR_ADJUDICATION)'),
      'stored_label_window_sec': [0.0, 24.0],
      'ground_truth': None,
      'note': ('stored window is juxtaposed for diagnostics only; the label set identity is '
               'untrusted so this is NOT an accuracy measurement'),
    },
    'tracking_video': {
      'input_video': CLIP,
      'target_description': 'the man in the white sleeveless shirt in the foreground',
      'first_frame_box': None,
      'ground_truth': None,
      'note': ('author GOT-10k protocol supplies a first-frame box; here a natural-language target '
               'description is used instead, so the initialisation prior DIFFERS from GOT-10k'),
    },
  },
}
out = f'{R}/evidence/sample_manifest.json'
with open(out, 'w') as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
    fh.write('\n')
print(json.dumps(manifest, indent=2, ensure_ascii=False))
print('\nwrote', out)

# what the model will actually see, computed the qwen_vl_utils way
import math
for name, fps, mx in (('temporal_grounding', 4, 2048), ('tracking', 1, 32)):
    n = int(round(clip_dur * fps)); n = max(4, min(mx, n)); n = max(1, min(n, clip_n))
    idx = [int(round(i)) for i in [ (clip_n - 1) * k / (n - 1) for k in range(n) ]] if n > 1 else [0]
    secs = [round(i / clip_fps, 3) for i in idx]
    print(f'  {name}: fps={fps} max_frames={mx} -> nframes={n} '
          f'first_idx={idx[:4]} last_idx={idx[-1]} '
          f'first_t={secs[:3]} last_t={secs[-1]}')
PY

echo
echo "=== PER-TASK BUDGETS (from author datasets.jsonl) ==="
cat <<'EOF'
spatial_grounding : min_pixels=65536  max_pixels=1048576   (min_tokens=64, total_tokens=1024, dr=32)
temporal_grounding: min_pixels=1024   max_pixels=409600    total_pixels=131072000 max_frames=2048 fps=4
tracking          : min_pixels=4096   max_pixels=786432    total_pixels=8388608   max_frames=32   fps=1
EOF
