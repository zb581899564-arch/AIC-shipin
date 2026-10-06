"""Independent schema and diagnostic metric helpers for the AIC task."""

from .schema import (
    BBox,
    ValidatedPrediction,
    VideoMeta,
    ValidationReport,
    load_media_metadata,
    validate_submission_records,
)
from .internal_metric import score_predictions

__all__ = [
    "BBox",
    "ValidatedPrediction",
    "VideoMeta",
    "ValidationReport",
    "load_media_metadata",
    "validate_submission_records",
    "score_predictions",
]
