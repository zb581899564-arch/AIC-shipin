"""Finish only the failed percent-encoded vs Unicode URL identity check.

No page/README reread, and no repeated successful attachment request: v1
failed before requesting any attachment. Preserve its original failure.
"""
import concurrent.futures
import json
from urllib.parse import unquote
from capture_primary_metadata import ROOT, REPORT, fetch, save


def main():
    target = REPORT / "official_rule_check_02.json"
    if target.exists():
        raise FileExistsError("Completed rule attachment check may not repeat")
    old = json.loads((REPORT / "primary_metadata_receipt_01.json").read_text())
    if old["attachments"]:
        raise ValueError("Resume must not repeat any successful attachment request")
    links = {unquote(url): url for page in old["pages"] for url in page["pdf_links"]}
    prior_path = ROOT / "reports/videoxum_reference_iteration_20261013_v1/official_rule_check_before_package_09.json"
    prior = json.loads(prior_path.read_text())
    originals = prior["attachments"]
    for item in originals:
        if unquote(item["url"]) not in links:
            raise ValueError("Actual normalized attachment URL differs: full new review needed")
    receipts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch, item["url"]): item for item in originals}
        for future in concurrent.futures.as_completed(futures):
            original = futures[future]
            data, receipt = future.result()
            receipt.update(current_page_literal_url=links[unquote(original["url"])],
                           URL_unicode_and_percent_encoding_identical=True,
                           same_as_prior_full_review=receipt["bytes"] == original["bytes"] and receipt["sha256"] == original["sha256"])
            receipts.append(receipt)
            if not receipt["same_as_prior_full_review"]:
                with (REPORT / "primary_metadata_01" / ("changed_attachment_02_" + str(len(receipts)) + ".pdf")).open("xb") as stream:
                    stream.write(data)
    ok = len(receipts) == 3 and all(r["same_as_prior_full_review"] for r in receipts)
    save(target, dict(status="CURRENT_PUBLIC_RULES_UNCHANGED" if ok else "STOP_FRESH_FULL_RULE_REVIEW_REQUIRED",
                      checked_date="2026-10-13", attachments=receipts,
                      full_text_review_reused_because_actual_bytes_identical=str(prior_path),
                      v1_original_failure_preserved=True, failure_was_URL_encoding_comparison_not_rule_change=True,
                      page_and_GitHub_metadata_success_not_repeated=True,
                      current_body_and_notice_catalog_read=True, new_video_supplement_found=False,
                      rule_interpretation="Automatic external-developed crop postprocessing is not explicitly prohibited; reproducibility, legal data, no test manual correction/reverse construction, and actual <=9B apply. This is interpretation, not organizer confirmation.",
                      crop_quality_admitted=False, new_model_calls=0, new_ZIPs=0))
    print(json.dumps(dict(status="CURRENT_PUBLIC_RULES_UNCHANGED" if ok else "STOP_RULE_BYTES_CHANGED", attachments=len(receipts))))


if __name__ == "__main__":
    main()
