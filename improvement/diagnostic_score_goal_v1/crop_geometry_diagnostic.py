"""New CPU-only GNMC candidate-geometry diagnostic, no media/model/fit access."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback
from typing import List, Tuple

import crop_geometry as geometry

HOME = Path('/home/inspur/aic_video_work')
A = HOME/'gnmc_width_iteration_20261013_v1'
D = HOME/'sprint45_spatial_width602_20261016_v1'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
SPATIAL = RUN/'b_score_aligned_package_v4/spatial_baseline.py'
MANIFEST_SHA = '296d487b55a50dfec5cc2c51fca98ee7a0cb8fd41c40868842b25a8b61e111e4'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


class Evidence:
    def __init__(self):
        self.files = {}

    def text(self, path, expected=None):
        path = Path(path).resolve()
        geometry.require(path.is_relative_to(HOME.resolve()) and path.is_file(), 'Missing/out-of-work-root evidence: '+str(path))
        digest = sha(path)
        geometry.require(expected is None or digest == expected, 'Frozen evidence SHA mismatch: '+str(path))
        geometry.require(str(path) not in self.files or self.files[str(path)] == digest, 'Evidence changed during diagnostic')
        self.files[str(path)] = digest
        return path.read_text(encoding='utf-8-sig')

    def read(self, path, expected=None):
        return json.loads(self.text(path, expected))

    def lines(self, path, expected=None):
        return [json.loads(line) for line in self.text(path, expected).splitlines() if line.strip()]


def frozen_helpers(evidence, lock):
    """Compile just the two already-frozen pure functions; import no model code."""
    text = evidence.text(SPATIAL, lock['external_files'][str(SPATIAL)])
    tree = ast.parse(text)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ('compute_crop_size', 'center_to_box')]
    geometry.require(len(nodes) == 2, 'Frozen spatial geometry functions missing')
    namespace = dict(math=math, List=List, Tuple=Tuple)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SPATIAL), 'exec'), namespace)
    return namespace['compute_crop_size'], namespace['center_to_box']


def verify_pool_with_frozen(boxes, width, height, baseline, compute, place):
    cw, _ = compute(width, height, 16, 9)
    geometry.require(cw == geometry.largest_width(width, height), 'Fixed max width differs from frozen pipeline')
    expected = [list(baseline)]; seen = {tuple(baseline)}
    for scale in geometry.SCALES_PERMILLE:
        w = max(1, cw*scale//1000)
        for cx in geometry.GRID_CENTERS:
            for cy in geometry.GRID_CENTERS:
                box = place(cx, cy, width, height, w, w*9/16)
                if tuple(box) not in seen:
                    expected.append(box); seen.add(tuple(box))
    geometry.require(boxes == expected, 'Candidate placement/order differs from frozen integer geometry')


def screen_diagnostic(evidence, compute, place, lock):
    acceptance = evidence.read(A/'input_acceptance.json')
    geometry.require(acceptance['status'] == 'PASS_FORTY_REAL_STATIC_RGB_EIGHTY_PROCESSOR_INPUTS'
            and acceptance['items'] == 40 and acceptance['stages'] == 80, 'Original40 input acceptance missing')
    items = evidence.read(A/'inputs.json', acceptance['input_sha256'])
    labels = evidence.read(A/'reference/labels.json', acceptance['labels_sha256'])
    geometry.require(len(items) == len(labels) == 40 and len({x['item_id'] for x in items}) == 40
            and len({x['item_id'] for x in labels}) == 40, 'Original40 input/reference denominator differs')
    refs = {x['item_id']: x for x in labels}
    geometry.require(set(refs) == {x['item_id'] for x in items}, 'Input/reference identities differ')
    completion = evidence.read(A/'recovery_01/screen/inference_completion.json')
    geometry.require(completion['status'] == 'EXECUTION_COMPLETE_NOT_QUALITY' and completion['items'] == 20
            and completion['calls'] == 40 and completion['optimizer_updates'] == 0
            and completion['source_lock_sha256'] == evidence.files[str((A/'recovery_01/source_lock.json').resolve())], 'Original screen execution/source binding differs')
    predictions = evidence.lines(A/'recovery_01/screen/predictions.jsonl', completion['predictions_sha256'])
    old = {x['item_id']: x for x in predictions}; screen = [x for x in items if x['role'] == 'screen']
    geometry.require(len(screen) == len(predictions) == len(old) == 20 and set(old) == {x['item_id'] for x in screen}, 'Exact original screen20 baseline coverage required')
    geometry.require(sum(x['role'] == 'confirm' for x in items) == 20, 'Original confirm20 denominator differs')
    rows = []
    for item in screen:
        key = item['item_id']; ref = refs[key]; baseline = old[key]; width, height = item['width'], item['height']
        geometry.dimensions(width, height)
        geometry.require(ref['role'] == item['role'] and ref['source_sha256'] == item['source_sha256'] == baseline['source_sha256']
                and item['ratio'] == [16, 9] and baseline['status'] == 'MODEL_OK', 'Screen source/ratio/success identity differs')
        proof_path = A/item['proof']
        proof = evidence.read(proof_path, lock['files'][str(proof_path.relative_to(A))])
        geometry.require(proof['item_id'] == key and proof['role'] == 'screen' and proof['source_sha256'] == item['source_sha256']
                and proof['dimensions'] == [width, height] and proof['reference_used_for_input'] is False, 'Original screen source dimensions/proof differ')
        cw, ch = compute(width, height, 16, 9)
        geometry.require(place(*baseline['center'], width, height, cw, ch) == baseline['baseline_box'], 'Cached baseline does not match frozen center placement')
        human = ref['reference_xywh']
        geometry.require(geometry.reference_from_normalized(ref['original_normalized_xyxy'], width, height) == human,
                         'Original float reference conversion differs; do not repair reference')
        boxes = geometry.candidate_pool(width, height, baseline['baseline_box'])
        verify_pool_with_frozen(boxes, width, height, baseline['baseline_box'], compute, place)
        best, oracle, scores = geometry.best_candidate(boxes, human)
        geometry.require(best >= 0 and oracle >= scores[0] and boxes[0] == baseline['baseline_box'], 'Oracle baseline containment failed')
        rows.append(dict(item_id=key, source_sha256=item['source_sha256'], width=width, height=height,
            original_baseline_box=baseline['baseline_box'], original_normalized_xyxy=ref['original_normalized_xyxy'],
            original_float_reference_xywh=human, reference_changed=False, baseline_iou=scores[0], oracle_iou=oracle,
            oracle_gain=oracle-scores[0], best_candidate_index_diagnostic_only=best,
            candidate_count=len(boxes), candidate_boxes=boxes, candidate_ious_reference_assisted=scores,
            baseline_included=True, all_candidates_legal=all(geometry.legal(box, width, height) for box in boxes)))
    return dict(scope='Previously exposed original screen20 static native16:9 only; no confirm baseline fabricated',
        sources=rows, count=20, mean_baseline_iou=sum(x['baseline_iou'] for x in rows)/20,
        mean_oracle_iou=sum(x['oracle_iou'] for x in rows)/20, mean_oracle_gain=sum(x['oracle_gain'] for x in rows)/20,
        improved_files=sum(x['oracle_gain'] > 0 for x in rows), baseline_wins_or_ties=sum(x['best_candidate_index_diagnostic_only'] == 0 for x in rows),
        minimum_candidate_count=min(x['candidate_count'] for x in rows), maximum_candidate_count=max(x['candidate_count'] for x in rows),
        oracle_is_prediction=False, old_screen_program_executed=False), items


def train_metadata_diagnostic(evidence, eval_items, compute, place):
    protocol = evidence.read(D/'protocol.json')
    geometry.require(protocol['schema'] == 'SPATIAL_WIDTH_LM602_ONLINE_EXPLORATION_V1'
            and protocol['data_use'] == 'studentNC' and protocol['known_exposure'] == 'HISTORICALLY_EXPOSED_AUTHOR_TRAIN602'
            and protocol['source_manifest_sha256'] == MANIFEST_SHA, 'Original602 registered research manifest differs')
    manifest = evidence.read(D/'source_manifest.json', MANIFEST_SHA)
    split = geometry.source_split(manifest)
    acceptance = evidence.read(D/'cpu_acceptance.json')
    geometry.require(acceptance['status'] == 'PASS_602_NEW_PURPOSE_JPEG_RGB_PREFIX_INPUTS'
            and acceptance['protocol_sha256'] == evidence.files[str((D/'protocol.json').resolve())]
            and acceptance['source_manifest_sha256'] == MANIFEST_SHA and acceptance['train'] == 602
            and acceptance['screen'] == acceptance['confirm'] == 0, 'Original602 input metadata binding differs')
    sources = acceptance['sources']
    geometry.require(len(sources) == 602 and len({s['id'] for s in sources}) == 602, '602 complete source metadata required')
    eval_ids = {x['item_id'] for x in eval_items}; eval_sha = {x['source_sha256'] for x in eval_items}
    geometry.require(not eval_ids & {x['id'] for x in manifest} and not eval_sha & {x['source_sha256'] for x in manifest}, 'Original40 eval identity/byte overlap entered fit split')
    rows = []
    for i, (item, source) in enumerate(zip(manifest, sources)):
        sample = 'I%04d' % i
        geometry.require(source['sample_id'] == sample and source['id'] == item['id']
                and source['source_sha256'] == item['source_sha256'] and source['source'] == item['source'], 'Fixed602 source order/JPEG binding differs')
        proof = evidence.read(D/'inputs'/sample/'proof.json')
        geometry.require(proof == source and proof['labels_in_input'] is False, 'Original input metadata proof differs')
        width, height = source['width'], source['height']
        human = geometry.reference_from_normalized(item['reference_original_xyxy'], width, height)
        error = geometry.validate_reference(human, width, height)
        # No model center exists for train602. The deterministic centered max
        # box is merely a grid anchor; never call it an observed model baseline.
        anchor = geometry.place_crop(width, height, (.5, .5))
        boxes = geometry.candidate_pool(width, height, anchor)
        verify_pool_with_frozen(boxes, width, height, anchor, compute, place)
        geometry.require(all(geometry.legal(box, width, height) for box in boxes), 'Training candidate escaped source boundary')
        rows.append(dict(id=item['id'], source_sha256=item['source_sha256'], sample_id=sample, width=width, height=height,
            proposed_future_role=split[item['id']], historical_exposure=True, blind_reference=False,
            candidate_count=len(boxes), all_candidates_legal=True, original_reference_legal=True,
            original_reference_aspect_height_error_pixels=error, reference_changed=False,
            geometric_anchor_box=anchor, anchor_is_observed_model_baseline=False))
    return dict(scope='Geometry metadata only, historical author-train602; no image bytes, optimizer, features or model scores read',
        rows=rows, sources=602, proposed_train=482, proposed_dev=120,
        split_rule=geometry.SPLIT_SALT+'source_sha256 ASCII, SHA256 ascending; first482 train, remaining120 dev',
        original_eval40_excluded_from_fit=True, global_source_independence='UNKNOWN', new_blind_sources=0,
        all_602_reference_legal=True, all_candidate_boundaries_legal=True,
        minimum_candidate_count=min(x['candidate_count'] for x in rows), maximum_candidate_count=max(x['candidate_count'] for x in rows),
        maximum_reference_aspect_height_error_pixels=max(x['original_reference_aspect_height_error_pixels'] for x in rows),
        fitting_or_training_admitted=False)


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main(root):
    geometry.require(sys.platform.startswith('linux') and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Must run as explicitly CUDA-masked Linux CPU child')
    root = root.resolve()
    geometry.require(root.is_relative_to(HOME.resolve()) and root not in (HOME, A, D)
            and not root.is_relative_to(A) and not root.is_relative_to(D), 'Distinct authorized new diagnostic root required')
    output = root/'crop_pool_diagnostic_01'; output.mkdir(parents=True, exist_ok=False)
    evidence = Evidence()
    try:
        purpose = evidence.read(A/'purpose_reply.json')
        geometry.require(purpose['answer'] == '仅学生参赛/科研，不涉及商业产品', 'Existing studentNC purpose binding missing')
        evidence.text(A/'control/LICENSE.txt')
        lock = evidence.read(A/'recovery_01/source_lock.json')
        compute, place = frozen_helpers(evidence, lock)
        screen, eval_items = screen_diagnostic(evidence, compute, place, lock)
        train = train_metadata_diagnostic(evidence, eval_items, compute, place)
        save(output/'result.json', dict(schema='GNMC_FIXED_CANDIDATE_GEOMETRY_DIAGNOSTIC_V1',
            status='COMPLETE_GEOMETRY_ORACLE_ONLY_NO_MODEL_OR_TRAINING_ADMISSION', screen20=screen, train602_metadata=train,
            candidate_policy=dict(ratio=[16, 9], scales_permille=geometry.SCALES_PERMILLE,
                grid_centers=geometry.GRID_CENTERS, width_rounding='floor(max_legal_width*permille/1000), minimum1',
                placement='frozen spatial_baseline center_to_box: clamp, Python round ties-even, y maximum floor(H-w*9/16+1e-9)',
                deduplication='Final legal integer[x,y,w], original baseline first; no reference-derived candidate'),
            evidence_files=evidence.files, source_code={str(Path(__file__).resolve()):sha(__file__), str(Path(geometry.__file__).resolve()):sha(geometry.__file__)},
            original_spatial_source= str(SPATIAL), original_reference_labels_changed=False,
            new_model_calls=0, new_training_updates=0, new_media_reads=0, old_screen_program_runs=0,
            official_score_claim=False, complete40_47_quality_claim=False, production_admitted=False,
            next_hypothesis_only='A distinct candidate-IoU predictor using spatial visual-patch ROI features; geometry oracle must first justify investing in it'))
        print(json.dumps(dict(status='COMPLETE_NEW_GEOMETRY_DIAGNOSTIC_ONLY', result=str(output/'result.json'), screen=20, train_metadata=602)))
    except BaseException as error:
        save(output/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), evidence_files=evidence.files,
             original_files_modified=False, fallback_or_reference_repair=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
