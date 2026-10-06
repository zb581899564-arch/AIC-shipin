# QVHighlights v2 data worker

`build_qvh_v2.py` creates deterministic query-moment-retrieval candidates
from the pinned Moment-DETR annotations. It preserves the official train/val
boundary, removes source groups present on both sides, splits official val
groups into dev/holdout, and validates every selected video with SHA-256 and
PyAV header/first-frame/final-frame checks.

The default `--source-trust pending` mode is fail closed: rows are aligned but
marked candidate-only, trusted counts stay zero, and the independent v2 gate
is rejected. `--source-trust confirmed` exists only for a later explicit
supervisor adjudication of the retained package-provenance evidence.
