"""Read the actual frozen DPO evidence; never train or change its STOP gate."""
import math
from .contracts import checked, reference, require, same_reference, strict_load


def diagnose(completion_path, review_path, workspace):
    completion_ref, review_ref = reference(completion_path), reference(review_path)
    complete = strict_load(checked(completion_ref, workspace))
    review = strict_load(checked(review_ref, workspace))
    require(complete.get("status") == "COMPLETE_PILOT_NOT_ADMITTED"
            and review.get("status") == "STOP_MECHANISM"
            and same_reference(review["pilot_completion_ref"], completion_ref),
            "Actual completed pilot plus its frozen STOP review required")
    count = complete["counts"]
    require(count["sequence_scores_completed"] == 258 and count["backwards_completed"] == 64
            and count["optimizer_steps"] == 16 and count["generations_completed"] == 43,
            "This diagnostic adopts the actual completed258/64/16/43 experiment")
    prepared = strict_load(checked(complete["prepared_ref"], workspace))
    pairs = {p["pair_id"]: p for p in prepared["check_pairs"]}
    scores = strict_load(checked(complete["heldout_pair_scores_ref"], workspace))
    original = {p["pair_id"]: p for p in scores["reference"]}
    policy = {p["pair_id"]: p for p in scores["policy"]}
    require(len(pairs) == len(prepared["check_pairs"]) == len(scores["reference"]) == len(scores["policy"]) == 16
            and set(pairs) == set(original) == set(policy), "Frozen check-pair denominator mismatch")
    rows = []
    for pid, pair in pairs.items():
        before, after = original[pid], policy[pid]
        require(all(type(row[key]) in (int, float) and math.isfinite(row[key])
                    for row in (before, after) for key in ("chosen_logprob", "rejected_logprob")),
                "Actual finite absolute log probabilities required")
        require(before["source_id"] == after["source_id"] == pair["source_id"], "Pair/source identity differs")
        a, b = pair["chosen_ids"], pair["rejected_ids"]
        require(a != b and len(a) == len(b), "This is the original matched-length reflection protocol")
        divergence = next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
        dc = after["chosen_logprob"] - before["chosen_logprob"]
        dr = after["rejected_logprob"] - before["rejected_logprob"]
        rows.append(dict(pair_id=pid, source_id=pair["source_id"], suffix_tokens=len(a),
            shared_suffix_prefix_tokens=divergence, chosen_absolute_logp_delta=dc,
            rejected_absolute_logp_delta=dr, relative_margin_delta=dc-dr,
            both_answers_absolute_logp_fell=dc < 0 and dr < 0,
            raw_margin_before=before["chosen_logprob"]-before["rejected_logprob"],
            raw_margin_after=after["chosen_logprob"]-after["rejected_logprob"],
            direct_shared_prefix_loss_gradient="EXACT_CANCELLATION_AT_IDENTICAL_CONTEXT"))
    return dict(schema="AIC_FROZEN_DPO_DIAGNOSTIC_V1", status="READ_ONLY_DIAGNOSTIC_COMPLETE",
        completion_ref=completion_ref, frozen_review_ref=review_ref,
        original_stop_reasons=review["stop_reasons"], original_stop_unchanged=True,
        pairs=rows, both_absolute_logps_fell=sum(row["both_answers_absolute_logp_fell"] for row in rows),
        actual_new_qwen_calls=0, new_training_updates=0,
        unavailable=["Private per-token logits/gradients if not recorded in original run",
                     "Causal attribution to feature insufficiency or dataset task shift",
                     "Official spatial reference or official effect"],
        next_minimal_evidence="Actual generated candidate diversity, full-source oracle/regret, visual-rotation scores; never change the DPO gate")
