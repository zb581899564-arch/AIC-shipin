      "media_bytes": 15043855,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\z_6gVvQb2d0\\z_6gVvQb2d0.mp4",
      "native_frames": 8281,
      "duration": 276.3093666666667,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    }
  ],
  "original_overlap_receipt": {
    "path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\corpus_acceptance.json",
    "sha256": "5d757bc62ab8fd18e603926f83c68c3593f6ab7e4c1f2ad6f4374af2ad5f3e81",
    "status": "NO_MATCH_IN_AVAILABLE_METADATA",
    "overlap": []
  },
  "unchanged_overlap_evidence": [
    {
      "path": "G:\\ai\\AIC视频\\data_audit\\video_inventory.tsv",
      "actual_sha256": "8225b1e7485c0657f82f00c6a11d57327f847907efaabe6a61076b7ed4c1507e",
      "comparison": "original 11-char source IDs and available exact hashes"
    },
    {
      "path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\controller\\m0_finalize_01\\clean_manifest_426.json",
      "actual_sha256": "57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32",
      "comparison": "exact encoded media hashes only; anonymized source identities unavailable"
    }
  ],
  "semantic_reencoded_duplicate_exclusion_proven": false,
  "limitations": "Existing exact hashes and available IDs only; no new semantic deduplication, test pixels, or blind evaluation claim. Historical license discrepancy retained, not adjudicated by this audit."
}
```

## 新必要原文件全文 reports/qwen8b_annotation_20261009_v1/corpus_acceptance.json
原始bytes=2384 SHA=5d757bc62ab8fd18e603926f83c68c3593f6ab7e4c1f2ad6f4374af2ad5f3e81

```
{
  "utc": "2026-10-09T08:08:31.990493+00:00",
  "status": "PASS_LOCAL_IDENTITIES_AND_FIXED_SPLIT",
  "sources": 50,
  "frames": 600,
  "split": {
    "validation": 10,
    "train": 40
  },
  "category_split": {
    "BK": {
      "train": 4,
      "validation": 1
    },
    "BT": {
      "train": 4,
      "validation": 1
    },
    "DS": {
      "validation": 1,
      "train": 4
    },
    "FM": {
      "train": 4,
      "validation": 1
    },
    "GA": {
      "train": 4,
      "validation": 1
    },
    "MS": {
      "train": 4,
      "validation": 1
    },
    "PK": {
      "train": 4,
      "validation": 1
    },
    "PR": {
      "validation": 1,
      "train": 4
    },
    "VT": {
      "train": 4,
      "validation": 1
    },
    "VU": {
      "train": 4,
      "validation": 1
    }
  },
  "source_overlap_status": "NO_MATCH_IN_AVAILABLE_METADATA",
  "overlap": [],
  "evidence": [
    {
      "path": "G:\\ai\\AIC视频\\data_audit\\video_inventory.tsv",
      "sha256": "8225b1e7485c0657f82f00c6a11d57327f847907efaabe6a61076b7ed4c1507e",
      "records": 11576,
      "available_hashes": 912,
      "comparison": "original 11-char source IDs and available exact hashes"
    },
    {
      "path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\controller\\m0_finalize_01\\clean_manifest_426.json",
      "sha256": "57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32",
      "records": 426,
      "available_hashes": 425,
      "comparison": "exact encoded media hashes only; anonymized source identities unavailable"
    }
  ],
  "human_frame_alignment_issues": [
    {
      "source_id": "Se3oxnaPsz0",
      "native_frames": 4166,
      "human_vector_length": 4165,
      "disposition": "EXCLUDE_HUMAN_VECTOR_ORDINAL_LABELS_UNTIL_ALIGNMENT_PROVEN"
    },
    {
      "source_id": "WG0MBPpPC6I",
      "native_frames": 9535,
      "human_vector_length": 9534,
      "disposition": "EXCLUDE_HUMAN_VECTOR_ORDINAL_LABELS_UNTIL_ALIGNMENT_PROVEN"
    }
  ],
  "semantic_or_reencoded_duplicate_exclusion_proven": false,
  "limitations": "Local identity metadata comparison does not exclude reencoded/partial duplicates or unknown original identities of rematch media. No contest pixels or test labels were read."
}

```

END_EMPTY407_P01
