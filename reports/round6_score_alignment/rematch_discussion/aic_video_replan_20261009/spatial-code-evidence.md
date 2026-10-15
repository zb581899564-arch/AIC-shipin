# 主控新只读空间代码证据

此处没有运行模型、重新验收旧CPU或修改冻结代码。静态代码并不能证明未检测到的真实镜头边界或主体语义正确。

## b_score_aligned_package_v4/field_contract.py / 完整文件
原文件SHA256 a968bc17f56e8757b5992679ed5f89fe2d70f9c9ea925d64bac52511cfb38a19

```python
"""CPU spatial-field contracts independent of any temporal selection.

The registered field domain is supplied by the caller; this module reads no
media. Full-domain shot analysis and same-frame anchors are frozen once. Every
anchor and interpolated field frame is validated before a selection is taken.
The caller supplies a legacy_manifest projection for native-clock manifests.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import PurePosixPath

try:
    from . import package_contract as package
except ImportError:
    import package_contract as package
from p2j_core import anchor_frames, box_is_legal, group_shots, interpolate_box


FIELD_FRAME_KEYS = {"video_id", "source_frame", "source_path", "source_width",
                    "source_height", "source_n_frames", "fps", "target_ratio_wh"}
REQUEST_KEYS = FIELD_FRAME_KEYS | {"kind", "expected_pixel_sha256", "anchor_request_sha256"}
MAX_GAP = 8


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _keys(rows, name):
    _require(isinstance(rows, list), name + " must be a list, including legal empty")
    for row in rows:
        _require(isinstance(row, dict) and isinstance(row.get("video_id"), str) and bool(row["video_id"]) and
                 type(row.get("source_frame")) is int and row["source_frame"] >= 0,
                 name + " has an invalid source-frame identity")
    return package.keyset(rows)


def _frame(row):
    _require(set(row) == FIELD_FRAME_KEYS, "field frame contains missing or unregistered fields")
    for name in ("source_width", "source_height", "source_n_frames"):
        _require(type(row[name]) is int and row[name] > 0, "invalid field source geometry")
    _require(row["source_frame"] < row["source_n_frames"], "field source frame is out of range")
    ratio = row["target_ratio_wh"]
    _require(isinstance(ratio, list) and ratio in ([9, 16], [16, 9]) and all(type(x) is int for x in ratio),
             "field target ratio is not registered")
    fps = row["fps"]
    _require(type(fps) in (int, float) and math.isfinite(fps) and fps > 0, "invalid field source fps")
    path = row["source_path"]
    _require(isinstance(path, str) and PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts,
             "invalid field source path")


def _shots(rows, metadata=None):
    keys = _keys(rows, "field shots")
    for row in rows:
        _require(type(row.get("is_shot_start")) is bool, "field shot start must be an explicit bool")
        _require(_sha(row.get("decoded_pixel_sha256")), "field shot pixel SHA256 is missing or invalid")
        if metadata is not None:
            m = metadata.get(row["video_id"])
            _require(m is not None and row["source_frame"] < m["n_frames"], "unregistered or out-of-range field shot")
    return keys


def _request_sha(row):
    # Identical canonical request identity to vendor/build_anchors.py.
    body = {key: row[key] for key in sorted(row) if key != "anchor_request_sha256"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _same_source(row, metadata):
    _frame(row)
    m = metadata.get(row["video_id"])
    _require(m is not None and row["source_path"] == m["source_path"] and
             row["source_width"] == m["width"] and row["source_height"] == m["height"] and
             row["source_n_frames"] == m["n_frames"] and row["target_ratio_wh"] == m["targetRatioWH"] and
             abs(row["fps"] - m["fps_num"] / m["fps_den"]) <= 1e-6,
             "field/selected source identity does not match registered manifest")


def build_field_requests(field_frames, field_shots, max_gap=8):
    """Freeze same-frame requests from the full registered field, never selected.

    Frame rows use the historical eight source fields. Shot rows use the
    sequential decoder's pixel SHA256 and explicit ``is_shot_start`` flag.
    Empty domains produce an empty request list without a call-reduction divide.
    """
    _require(type(max_gap) is int and max_gap == MAX_GAP, "the registered field anchor max gap is 8")
    frame_keys = _keys(field_frames, "field frames")
    shot_keys = _shots(field_shots)
    _require(frame_keys == shot_keys, "field shot keys must exactly cover field frame keys")
    frames = {(row["video_id"], row["source_frame"]): row for row in field_frames}
    identities = {}
    for row in field_frames:
        _frame(row)
        identity = {key: row[key] for key in FIELD_FRAME_KEYS - {"source_frame"}}
        previous = identities.setdefault(row["video_id"], identity)
        _require(identity == previous, "field source identity changes within a video")
    shot_map = {(row["video_id"], row["source_frame"]): row for row in field_shots}
    anchors = set()
    for shot in group_shots(field_shots):
        vid = shot[0]["video_id"]
        anchors.update((vid, f) for f in anchor_frames([row["source_frame"] for row in shot], MAX_GAP))
    result = []
    for key in sorted(anchors):
        source = dict(frames[key])
        source["target_ratio_wh"] = list(source["target_ratio_wh"])
        source["kind"] = "QWEN_ANCHOR_SAME_FRAME"
        source["expected_pixel_sha256"] = shot_map[key]["decoded_pixel_sha256"]
        source["anchor_request_sha256"] = _request_sha(source)
        result.append(source)
    return result


def compose_from_field(manifest, selected, field_shots, requests, outputs):
    """Validate/interpolate the entire frozen field, then take selected frames.

    A failure on an unselected field anchor still blocks composition. Predictions
    contain every registered video, including videos with an empty selection;
    provenance contains exactly selected frames and fixed field shot identities.
    """
    metadata = package.validate_manifest(manifest)
    chosen = _keys(selected, "selected")
    field_keys = _shots(field_shots, metadata)
    request_keys, output_keys = _keys(requests, "field requests"), _keys(outputs, "field outputs")
    _require(chosen <= field_keys, "selected frame lies outside the registered field")
    _require(request_keys == output_keys, "field request/output key coverage mismatch")
    for row in selected:
        _same_source(row, metadata)
    shot_map = {(row["video_id"], row["source_frame"]): row for row in field_shots}
    grouped = group_shots(field_shots)
    scheduled_keys = {
        (shot[0]["video_id"], frame)
        for shot in grouped
        for frame in anchor_frames([row["source_frame"] for row in shot], MAX_GAP)
    }
    _require(request_keys == scheduled_keys, "field anchor schedule lacks endpoint/intermediate or differs from actual-shot max-gap-8 rule")
    request_map = {(row["video_id"], row["source_frame"]): row for row in requests}
    output_map = {(row["video_id"], row["source_frame"]): row for row in outputs}
    for key, request in request_map.items():
        _require(set(request) == REQUEST_KEYS, "field request contains missing or unregistered fields")
        _same_source({name: request[name] for name in FIELD_FRAME_KEYS}, metadata)
        _require(request["kind"] == "QWEN_ANCHOR_SAME_FRAME" and
                 _sha(request["expected_pixel_sha256"]) and
                 request["expected_pixel_sha256"] == shot_map[key]["decoded_pixel_sha256"] and
                 _sha(request["anchor_request_sha256"]) and
                 request["anchor_request_sha256"] == _request_sha(request),
                 "field request SHA256 or same-frame pixel identity mismatch")
        output, m = output_map[key], metadata[key[0]]
        _require(output.get("status") == "MODEL_OK" and output.get("used_fallback") is False and
                 output.get("spatial_source") == "QWEN_ANCHOR_SAME_FRAME" and
                 output.get("anchor_request_sha256") == request["anchor_request_sha256"] and
                 output.get("decoded_pixel_sha256") == request["expected_pixel_sha256"] and
                 box_is_legal(output.get("box_xyw"), m["width"], m["height"], *m["targetRatioWH"]),
                 "field anchor failure, illegal box or source identity mismatch")
    full_predictions = {vid: [] for vid in metadata}
    full_provenance = []
    for shot_id, shot in enumerate(grouped):
        vid = shot[0]["video_id"]
        m = metadata[vid]
        frames = [row["source_frame"] for row in shot]
        anchors = {f: output_map[(vid, f)]["box_xyw"] for f in anchor_frames(frames, MAX_GAP)}
        for frame in frames:
            box, source = interpolate_box(frame, anchors)
            _require(box_is_legal(box, m["width"], m["height"], *m["targetRatioWH"]), "illegal interpolated field box")
            full_predictions[vid].append({"frame": frame, "bboxes": box})
            full_provenance.append({"video_id": vid, "source_frame": frame, "shot_id": shot_id,
                                    "box_xyw": box, "legal": True, **source})
    full_rows = [{"video_id": vid, "targetRatioWH": m["targetRatioWH"],
                  "predictions": sorted(full_predictions[vid], key=lambda item: item["frame"])}
                 for vid, m in sorted(metadata.items())]
    package.validate_predictions(manifest, full_rows, field_keys, full_provenance)
    rows = [{"video_id": row["video_id"], "targetRatioWH": row["targetRatioWH"],
             "predictions": [item for item in row["predictions"] if (row["video_id"], item["frame"]) in chosen]}
            for row in full_rows]
    provenance = [row for row in full_provenance if (row["video_id"], row["source_frame"]) in chosen]
    package.validate_predictions(manifest, rows, chosen, provenance)
    return rows, provenance

```

## baseline_a_pts_v1/vendor/p2j_core.py / 原文件L61-L183，未共享无关CLI/旧fallback路径
原文件SHA256 db660d8afe562f56ade048fc3de57c83354308ce2ca7e12856010b6341d80e6c

```python
def legal_crop_width(width: int, height: int, target_w: float, target_h: float) -> int:
    if width <= 0 or height <= 0 or target_w <= 0 or target_h <= 0:
        raise ValueError("invalid geometry")
    crop_w = width if width / height < target_w / target_h else int(
        math.floor(height * target_w / target_h + 1e-12))
    while crop_w > 1 and crop_w * target_h > height * target_w:
        crop_w -= 1
    return crop_w


def box_is_legal(box: Sequence, width: int, height: int,
                 target_w: float, target_h: float) -> bool:
    if not isinstance(box, (list, tuple)) or len(box) != 3:
        return False
    if any(isinstance(x, bool) or not isinstance(x, int) for x in box):
        return False
    x, y, crop_w = box
    crop_h = crop_w * target_h / target_w
    return (crop_w > 0 and x >= 0 and y >= 0 and x + crop_w <= width
            and math.isfinite(crop_h) and crop_h > 0
            and y + crop_h <= height + 1e-7)


def canonical_ratio(values: Sequence) -> list[int | float]:
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        raise ValueError("target ratio must contain two numbers")
    out: list[int | float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(value) or value <= 0:
            raise ValueError("invalid target ratio")
        out.append(int(value) if float(value).is_integer() else float(value))
    return out


def group_shots(analysis_rows: Sequence[Mapping]) -> list[list[dict]]:
    if not analysis_rows:
        return []
    rows = sorted((dict(x) for x in analysis_rows),
                  key=lambda x: (str(x["video_id"]), int(x["source_frame"])))
    keys = [(str(x["video_id"]), int(x["source_frame"])) for x in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate analyzed frame")
    shots: list[list[dict]] = []
    current: list[dict] = []
    previous: tuple[str, int] | None = None
    for row in rows:
        key = (str(row["video_id"]), int(row["source_frame"]))
        declared = bool(row.get("is_shot_start"))
        discontinuity = previous is None or key[0] != previous[0] or key[1] != previous[1] + 1
        if not current or declared or discontinuity:
            if current:
                shots.append(current)
            current = [row]
        else:
            current.append(row)
        previous = key
    if current:
        shots.append(current)
    return shots


def anchor_frames(frames: Sequence[int], max_gap: int) -> list[int]:
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap <= 0:
        raise ValueError("max_gap must be a positive integer")
    values = [int(x) for x in frames]
    if not values or values != sorted(set(values)):
        raise ValueError("frames must be a non-empty sorted unique sequence")
    if any(b != a + 1 for a, b in zip(values, values[1:])):
        raise ValueError("one anchor schedule cannot cross a frame discontinuity")
    anchors = list(values[::max_gap])
    if anchors[-1] != values[-1]:
        anchors.append(values[-1])
    if any(b - a > max_gap for a, b in zip(anchors, anchors[1:])):
        raise AssertionError("anchor schedule exceeded max_gap")
    return anchors


def interpolate_box(frame: int, anchors: Mapping[int, Sequence[int]]) -> tuple[list[int], dict]:
    ordered = sorted(int(x) for x in anchors)
    if frame in anchors:
        return [int(x) for x in anchors[frame]], {
            "spatial_source": "QWEN_ANCHOR_SAME_FRAME",
            "left_anchor": frame, "right_anchor": frame,
            "left_distance": 0, "right_distance": 0,
        }
    pos = bisect_left(ordered, frame)
    if pos == 0 or pos == len(ordered):
        raise ValueError("frame is not bracketed by anchors")
    left, right = ordered[pos - 1], ordered[pos]
    alpha = (frame - left) / (right - left)
    box = [int(round(float(anchors[left][i])
                     + alpha * (float(anchors[right][i]) - float(anchors[left][i]))))
           for i in range(3)]
    return box, {
        "spatial_source": "SHOT_LINEAR_INTERPOLATION",
        "left_anchor": left, "right_anchor": right,
        "left_distance": frame - left, "right_distance": right - frame,
    }


def xyw_iou(a: Sequence[int], b: Sequence[int], target_w: float = 9,
            target_h: float = 16) -> float:
    ax, ay, aw = (float(x) for x in a)
    bx, by, bw = (float(x) for x in b)
    ah, bh = aw * target_h / target_w, bw * target_h / target_w
    inter = max(0.0, min(ax + aw, bx + bw) - max(ax, bx)) * max(
        0.0, min(ay + ah, by + bh) - max(ay, by))
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0

```

## b_score_aligned_package_v4/production.py / 原文件L140-L198，未共享无关CLI/旧fallback路径
原文件SHA256 84472fdd4af0910265ccd13f95c1a42eb0712c8f9fe6fc0869bb837ee7af1218

```python
def spatial(scope,out):
    config=verify();_,manifest,clocks=inputs(scope);out=Path(out)
    require(read(out/'schedule.stage.json')['status']=='PASS_TIME_INDEPENDENT_SOURCE_FIELD','field schedule missing')
    requests=rows(out/'anchor_requests.jsonl')
    if not requests:
        write_rows(out/'anchor_output.jsonl',[])
        write(out/'spatial.stage.json',dict(status='PASS_EMPTY_SPACE_NO_MODEL_CALL',rows=0,invalid=0,
            model_calls=0,wall_seconds=0,measured_seconds_per_anchor=None,logical_parameters=8767123696))
        return
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from frame_contract import validate_frame_request
    from contracts import parse_focus_norm
    from PIL import Image
    import cv2
    baseline=load(HERE/'spatial_baseline.py','next_strict_spatial_baseline')
    model=baseline.Qwen3VL(config['model_dir'],device_map={'':'cuda:0'})
    require(sum(p.numel() for p in model.model.parameters())==8767123696,'space model parameter count changed')
    for parameter in model.model.parameters():parameter.requires_grad_(False)
    from engine import frozen_identity
    base_hash=frozen_identity(model.model,config)
    metadata={r['video_id']:r for r in manifest['records']};current=None;reader=None;failed=0;seconds=[];started=time.monotonic()
    with (out/'anchor_output.jsonl').open('x',encoding='utf-8') as stream:
        try:
            for n,request in enumerate(requests,1):
                one=time.monotonic();item=validate_frame_request(request,metadata)
                rec=dict(video_id=request['video_id'],source_frame=request['source_frame'],status='INFERENCE_FAILURE',
                    used_fallback=False,spatial_source='QWEN_ANCHOR_SAME_FRAME',
                    anchor_request_sha256=request['anchor_request_sha256'])
                try:
                    if current!=item['video_id']:
                        if reader is not None:reader.close()
                        require(sha(item['source_path'])==item['source_sha256'],'spatial source bytes changed')
                        current=item['video_id'];reader=OrdinalReader(item,clocks[current])
                    frame,pixel=reader.get(request['source_frame']);rec['decoded_pixel_sha256']=pixel
                    require(pixel==request['expected_pixel_sha256'],'same-frame pixel identity mismatch')
                    image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));tw,th=request['target_ratio_wh']
                    raw=model.predict_focus(image,(tw,th),max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
                    rec['raw_output']=raw;center=parse_focus_norm(raw,image.width,image.height)
                    require(center is not None,'strict integer JSON center failed; no unit guessing')
                    cw,ch=baseline.compute_crop_size(image.width,image.height,tw,th)
                    box=baseline.center_to_box(*center,image.width,image.height,cw,ch)
                    require(baseline.validate_box(box,image.width,image.height,tw,th),'illegal crop')
                    rec.update(status='MODEL_OK',box_xyw=[int(x) for x in box],center_norm=center)
                except Exception as exc:rec['error']=type(exc).__name__+': '+str(exc)
                rec['seconds']=time.monotonic()-one;seconds.append(rec['seconds']);failed+=rec['status']!='MODEL_OK'
                stream.write(json.dumps(rec,ensure_ascii=False)+'\n');stream.flush()
                if n%50==0 or n==len(requests):progress(out,dict(stage='SOURCE_FIELD_SPATIAL',anchors=n,
                    total=len(requests),failures=failed,wall_seconds=time.monotonic()-started))
        finally:
            if reader is not None:reader.close()
    write(out/'spatial.stage.json',dict(status='PASS_STRICT_SOURCE_FIELD_SPATIAL' if not failed else 'STOP_SPACE_FAILURE',
        rows=len(requests),invalid=failed,model_calls=len(requests),wall_seconds=time.monotonic()-started,
        measured_seconds_per_anchor=sum(seconds)/len(seconds),logical_parameters=8767123696,
        base_hash=base_hash,strict_units='INTEGER_0_TO_1000',time_adapter_enabled=False,failure_to_empty_conversions=0))
    require(failed==0,'space failures block candidate')

def finish(scope,out):
    config=verify();_,manifest,clocks=inputs(scope);out=Path(out)

```

## b_score_aligned_package_v4/spatial_baseline.py / 原文件L115-L178，未共享无关CLI/旧fallback路径
原文件SHA256 f8bb3303fae4866a9af34ab04c18313d0729ed05da4b7979330f4b1dd7a61245

```python

    The official evaluator derives ``h = w * target_h / target_w`` from the
    submitted triplet.  ``round`` can produce a width whose implicit height
    is larger than the source (e.g. width 169 for a 300px-high 9:16 frame),
    so the free dimension is floored and checked with exact cross-products.
    """
    if W <= 0 or H <= 0 or tw <= 0 or th <= 0:
        return max(1, W), float(max(1, H))
    target = tw / th
    if W / float(H) >= target:
        # Full source height is the largest fit in real-valued geometry, but
        # the submitted width must be an integer whose derived h is <= H.
        cw = min(W, max(1, int(math.floor((H * tw) / th + 1e-12))))
    else:
        # Full source width already fits by this branch.  Keep a final guard
        # for floating-point boundaries and unusual metadata.
        cw = W
    while cw > 1 and cw * th > H * tw:
        cw -= 1
    h_float = cw * th / tw
    if h_float > H + 1e-9:
        raise AssertionError(f"illegal crop geometry W={W} H={H} cw={cw} h={h_float}")
    return max(1, cw), h_float


def center_to_box(cx: float, cy: float, W: int, H: int, cw: int,
                  h_float: float) -> List[int]:
    """Place a crop around a normalized center and clamp to legal integers."""
    px = cx * W - cw / 2.0
    py = cy * H - h_float / 2.0
    max_x = max(0, W - cw)
    # y is integer while h is evaluator-derived float, therefore floor the
    # maximum y instead of rounding it upward at a fractional boundary.
    max_y = max(0, int(math.floor(H - h_float + 1e-9)))
    x = int(round(max(0.0, min(px, float(max_x)))))
    y = int(round(max(0.0, min(py, float(max_y)))))
    if x > max_x:
        x = max_x
    if y > max_y:
        y = max_y
    return [x, y, int(cw)]


def validate_box(box: Sequence[int], W: int, H: int, tw: float, th: float) -> bool:
    if len(box) != 3 or any(not isinstance(v, int) for v in box):
        return False
    x, y, w = box
    if w <= 0 or x < 0 or y < 0 or x + w > W:
        return False
    h = w * th / tw
    return h > 0 and y + h <= H + 1e-7


def parse_focus_norm(text: str, W: Optional[int] = None, H: Optional[int] = None) -> Optional[List[float]]:
    """Strict 0..1000 integer JSON center, uniformly normalized; no fallback."""
    from contracts import parse_focus_norm as strict_parse
    return strict_parse(text, W, H)


def parse_segments_sec(text: str) -> List[Tuple[float, float]]:
    """Parse ``{"segments": [[start, end], ...]}`` from model text."""
    for match in re.finditer(r"\{(?:[^{}]|\{[^{}]*\})*\}", text or "", re.S):
        try:
            obj = json.loads(match.group(0))

```

## b_score_aligned_package_v4/spatial_baseline.py / 原文件L382-L401，未共享无关CLI/旧fallback路径
原文件SHA256 f8bb3303fae4866a9af34ab04c18313d0729ed05da4b7979330f4b1dd7a61245

```python
    def predict_focus(self, pil_img: Image.Image, target_ratio: Sequence[float],
                      max_new_tokens: int) -> str:
        tw, th = target_ratio
        prompt = (
            "Below is a video frame to be re-framed (cropped) to %d:%d.\n"
            "Point out the center of the most important subject or region to "
            "keep. Use normalized integer coordinates in range 0~1000: x is "
            "horizontal (0=left, 1000=right), y is vertical (0=top, "
            "1000=bottom).\n"
            "Output ONLY JSON (no other text): {\"center\": [x, y]}"
            % (int(tw), int(th))
        )
        messages = [{"role": "user", "content": [
            {"type": "image", "image": pil_img, "max_pixels": self.max_pixels},
            {"type": "text", "text": prompt},
        ]}]
        return self._generate(messages, max_new_tokens)

    def reset_peak_memory(self) -> None:
        if self.torch.cuda.is_available():

```

静态观察：compose_from_field按group_shots拆分后分别构建anchors并插值；group_shots在显式is_shot_start或ordinal不连续时分割。所以“修复跨已登记镜头插值”须先指出可复现反例，不能把已有分镜机制当尚未实现。production.spatial的实际严格路径只用predict_focus中心，compute_crop_size固定最大合法尺度，parse失败即失败，未调用旧CLI fallback。插值改变不等于新锚点生成，也不等于原空间场exact复用。
