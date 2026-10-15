"""Pure elimination of calls with provably zero possible native-frame effect.

The rule is independent of video content, labels, scores, and learned answers.
For a validated native interval I and immutable protected baseline B, if I is
a subset of B then B union K equals B for every legal KEEP set K within I.

It may plan a whole view or an already accepted B0 segment as unnecessary.
It never claims a model answer, LEGAL_EMPTY, UNKNOWN, CPU QA or quality PASS.
Actual controllers must bind the baseline ZIP, clock, plan and this code, and
account for every omitted call with its complete native coverage witness.
Equivalence concerns final native-frame predictions/inherited boxes, not an
unobserved continuous-time interval list or a new human-summary metric.
"""
import hashlib
import json


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


class ProtectedNativeFrames:
    def __init__(self, total_frames, baseline_frames):
        require(type(total_frames) is int and total_frames > 0, 'Positive original native frame count required')
        values = list(baseline_frames)
        require(all(type(frame) is int and 0 <= frame < total_frames for frame in values),
                'Baseline ordinal must be an in-domain non-bool integer')
        require(len(set(values)) == len(values), 'Duplicate baseline ordinal cannot be hidden')
        self.total_frames = total_frames
        self.frames = frozenset(values)
        self.identity = hashlib.sha256(json.dumps(dict(total_frames=total_frames,
            baseline_frames=sorted(values)), separators=(',', ':'), sort_keys=True).encode()).hexdigest()

    def inspect(self, first, stop):
        """Use all eligible native frames, never just the 64 shown samples."""
        require(type(first) is int and type(stop) is int and 0 <= first < stop <= self.total_frames,
                'Positive exact half-open native interval required; empty/failed membership is not a skipped call')
        missing = sum(frame not in self.frames for frame in range(first, stop))
        proven = missing == 0
        return dict(schema='PROTECTED_BASELINE_NATIVE_NO_DELTA_PROOF_V1',
            status='PROVEN_NO_POSSIBLE_NATIVE_ADDITION' if proven else 'POTENTIAL_NATIVE_ADDITION_REQUIRES_NORMAL_EXECUTION',
            baseline_native_set_sha256=self.identity, source_total_frames=self.total_frames,
            first_native_ordinal=first, stop_native_ordinal=stop,
            complete_interval_native_count=stop-first, missing_baseline_native_frames=missing,
            all_native_interval_frames_already_in_baseline=proven,
            invariant='FOR_ALL_K_SUBSET_I__B_UNION_K_EQUALS_B' if proven else None,
            output_equivalence_scope='FINAL_NATIVE_FRAME_SET_WITH_ORIGINAL_BASELINE_BOXES',
            no_test_label_content_or_ranking_parameter_used=True,
            model_decision=None, model_calls_performed_by_this_module=0,
            quality_pass_claimed=False, actual_execution_or_QA_claimed=False)
