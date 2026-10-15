"""Verify delivered nested ZIPs and metadata identities without media decoding."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import io
import json
import stat
import zipfile

from inspect_download import member_path, save
import tarfile

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/tvsum/ydata-tvsum50-v1_1"


def main():
    archives = []
    video_ids = []
    info_rows = []
    annotations = []
    mat = None
    for path in sorted(DATA.glob("*.zip")):
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            seen = set()
            for member in members:
                member_path(tarfile.TarInfo(member.filename))
                key = member.filename.casefold()
                if key in seen:
                    raise ValueError("Duplicate ZIP member")
                seen.add(key)
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError("ZIP symlink rejected")
                if member.flag_bits & 1:
                    raise ValueError("Encrypted ZIP member")
            bad = archive.testzip()
            if bad is not None:
                raise ValueError("ZIP CRC failure: " + bad)
            regular = [m for m in members if not m.is_dir()]
            archives.append({"file": path.name, "status": "PASS_ALL_MEMBER_PATHS_AND_CRC",
                             "members": len(members), "regular_files": len(regular),
                             "payload_bytes": sum(m.file_size for m in regular),
                             "files": [{"name": m.filename, "bytes": m.file_size, "crc32": m.CRC}
                                       for m in regular]})
            for member in regular:
                suffix = Path(member.filename).suffix.lower()
                if path.name.endswith("-video.zip") and suffix in {".mp4", ".avi", ".mov", ".mkv"}:
                    video_ids.append(Path(member.filename).stem)
                if member.filename.endswith("ydata-tvsum50-info.tsv"):
                    text = archive.read(member).decode("utf-8-sig")
                    info_rows = [line.split("\t") for line in text.splitlines() if line.strip()]
                    if info_rows[0] != ["category", "video_id", "title", "url", "length"]:
                        raise ValueError("Unexpected explicit TSV header")
                    info_rows = info_rows[1:]
                if member.filename.endswith("ydata-tvsum50-anno.tsv"):
                    text = archive.read(member).decode("utf-8-sig")
                    annotations = [line.split("\t") for line in text.splitlines() if line.strip()]
                if member.filename.endswith("ydata-tvsum50.mat"):
                    mat = archive.read(member)
    if len(archives) != 4:
        raise ValueError("Expected four nested archives")
    if len(video_ids) != 50 or len(set(video_ids)) != 50:
        raise ValueError("Expected 50 distinct video entries")
    if len(info_rows) != 50 or len(annotations) != 1000:
        raise ValueError("Metadata/annotation denominator mismatch")
    if any(len(row) != 5 for row in info_rows) or any(len(row) != 3 for row in annotations):
        raise ValueError("Unexpected TSV field count")
    info_ids = {row[1] for row in info_rows}
    annotator_counts = Counter(row[0] for row in annotations)
    if info_ids != set(video_ids) or set(annotator_counts) != info_ids:
        raise ValueError("Video/metadata/annotation identities differ")
    if set(annotator_counts.values()) != {20}:
        raise ValueError("Expected twenty annotation rows per video")
    score_count = 0
    vector_lengths = {}
    for video_id, category, scores in annotations:
        values = [int(value) for value in scores.split(",")]
        if not values or not all(1 <= value <= 5 for value in values):
            raise ValueError("Invalid importance score")
        score_count += len(values)
        previous = vector_lengths.setdefault(video_id, len(values))
        if previous != len(values):
            raise ValueError("Judges have different vector lengths")
    by_id = {row[1]: row for row in info_rows}
    if any(category != by_id[video_id][0] for video_id, category, _ in annotations):
        raise ValueError("Annotation category mismatch")
    if mat is None:
        raise ValueError("MATLAB metadata missing")
    import h5py
    import numpy as np
    with h5py.File(io.BytesIO(mat), "r") as store:
        table = store["tvsum50"]
        if table["video"].shape != (50, 1):
            raise ValueError("Unexpected MATLAB table cardinality")
        for index in range(50):
            def get(name):
                return store[table[name][index, 0]][()]
            video_id = "".join(chr(int(char)) for char in get("video").ravel())
            nframes = int(get("nframes").item())
            user = get("user_anno")
            mean = get("gt_score")
            if vector_lengths[video_id] != nframes or user.shape != (20, nframes):
                raise ValueError("TSV vectors/MAT nframes identity mismatch")
            raw_rows = [row for row in annotations if row[0] == video_id]
            tsv_values = np.array([[int(v) for v in row[2].split(",")] for row in raw_rows])
            if not np.array_equal(tsv_values, user):
                raise ValueError("TSV scores/MAT user scores differ")
            if mean.shape != (1, nframes) or not np.allclose(mean[0], user.mean(axis=0), rtol=0, atol=1e-12):
                raise ValueError("Stored consensus differs from exact judge mean")
    save("tvsum_catalog.json", {
        "status": "METADATA_ONLY_NOT_TRAINING_ADMITTED",
        "sources": [{"source_id": row[1], "source_group": "youtube:" + row[1],
                     "category": row[0], "title": row[2], "source_url": row[3],
                     "duration_nominal_mmss": row[4],
                     "annotation_vector_length": vector_lengths[row[1]], "human_annotation_rows": 20,
                     "label_vector_mapping": "Matches stored MATLAB nframes; decoded native clock not yet verified",
                     "license_state": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README",
                     "external_teacher_upload_admitted": False,
                     "training_admitted": False,
                     "source_overlap_audit": "NOT_RUN",
                     "native_frame_clock_verified": False} for row in info_rows],
    })
    receipt = {
        "status": "PASS_LOCAL_DELIVERY_CRC_AND_METADATA_IDENTITY_LICENSE_UNRESOLVED",
        "utc": datetime.now(timezone.utc).isoformat(),
        "nested_archives": archives,
        "video_entries": len(video_ids), "metadata_rows": len(info_rows),
        "annotation_rows": len(annotations), "judges_per_video": 20,
        "importance_score_count": score_count,
        "category_counts": dict(Counter(row[0] for row in info_rows)),
        "all_video_metadata_annotation_ids_equal": True,
        "all_annotation_scores_in_1_to_5": True,
        "all_tsv_mat_user_scores_and_consensus_equal": True,
        "dense_score_entries_are_not_independent_judgments": True,
        "video_decode_performed": False,
        "training_admitted": False, "external_teacher_upload_admitted": False,
        "license_notice": "Bundled signed Yahoo agreement restriction conflicts with apparent current direct author distribution; no override presumed",
    }
    save("tvsum_delivery_acceptance.json", receipt)
    print(json.dumps({key: receipt[key] for key in (
        "status", "video_entries", "metadata_rows", "annotation_rows",
        "judges_per_video", "importance_score_count", "category_counts")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
