"""Explicit native32k profile entry using unchanged first-A0 runtime functions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.append('/home/inspur/aic_video_work/sprint_audio_events_20261021_v1/code')
import common
common.ROOT = common.ROOT/'native32k10'

if sys.argv[1] not in ['native_inputs10', 'events', 'event_review', 'text_inputs', 'time_calls', 'review']:
    raise ValueError('Only registered exact profile phases are allowed')
__import__(sys.argv[1]).main()
