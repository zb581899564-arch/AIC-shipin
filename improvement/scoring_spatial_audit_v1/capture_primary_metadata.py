"""Capture current primary rules and crop-source README/license metadata only."""
from __future__ import annotations

import base64
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports/scoring_spatial_audit_20261013_v1"
PAGES = ("https://www.aicomp.cn/tracks/tracks-6/4267.html",
         "https://www.aicomp.cn/notice/notice-3/5307.html",
         "https://www.aicomp.cn/notice/notice-3")
REPOS = ("aneeshvartakavi/GNMC", "HuiZeng/Grid-Anchor-based-Image-Cropping-Pytorch",
         "yiling-chen/flickr-cropping-dataset", "steven413d/LIVE-YT-VideoCropping",
         "suyukun666/S2CNet")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AIC-rule-readonly-audit"})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(3_000_001)
        if len(data) > 3_000_000:
            raise ValueError("Metadata response exceeded bounded request")
        return data, dict(url=url, final_url=response.url, status=response.status,
                          bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def repo_metadata(repo):
    def gh(arguments):
        raw = subprocess.run(["gh", *arguments], capture_output=True, timeout=45)
        if raw.returncode:
            raise RuntimeError(raw.stderr.decode(errors="replace"))
        return json.loads(raw.stdout)
    description = gh(["repo", "view", repo, "--json", "url,licenseInfo,pushedAt"])
    readme = gh(["api", f"repos/{repo}/readme"])
    raw = base64.b64decode(readme["content"])
    folder = REPORT / "primary_metadata_01"
    folder.mkdir(exist_ok=True)
    path = folder / (repo.replace("/", "__") + "__README.md")
    with path.open("xb") as stream:
        stream.write(raw)
    result = dict(repo=repo, **description, readme_path=str(path.relative_to(ROOT)),
                  readme_bytes=len(raw), readme_blob_sha=readme["sha"],
                  data_license_not_inferred_from_code_license=True, downloaded_media=0,
                  downloaded_model_weights=0)
    if description["licenseInfo"]:
        license = gh(["api", f"repos/{repo}/license"])
        license_raw = base64.b64decode(license["content"])
        with (folder / (repo.replace("/", "__") + "__LICENSE.txt")).open("xb") as stream:
            stream.write(license_raw)
        result["repo_license_name"] = license.get("license", {}).get("name")
        result["repo_license_blob_sha"] = license["sha"]
    return result


def main():
    target = REPORT / "primary_metadata_receipt_01.json"
    if target.exists():
        raise FileExistsError("Primary metadata capture already finished")
    REPORT.mkdir(parents=True, exist_ok=True)
    pages, attachments, repos, failures = [], [], [], []
    previous = json.loads((ROOT / "reports/videoxum_reference_iteration_20261013_v1/official_rule_check_before_package_09.json").read_text(encoding="utf-8"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(fetch, url): url for url in PAGES}
        for future in concurrent.futures.as_completed(jobs):
            url = jobs[future]
            try:
                data, receipt = future.result()
                text = data.decode("utf-8")
                pdf_links = sorted(set(re.findall(r'href=[\"\']([^\"\']+\.pdf)[\"\']', text)))
                receipt["pdf_links"] = pdf_links
                pages.append(receipt)
                path = REPORT / "primary_metadata_01" / ("official_page_" + str(PAGES.index(url) + 1) + ".html")
                path.parent.mkdir(exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(data)
            except Exception as exc:
                failures.append(dict(stage="page", url=url, error=repr(exc)))
    discovered = {link for page in pages for link in page["pdf_links"]}
    # Current pages MUST still point to the registered attachment URLs. Compare
    # raw bytes to the already fully read rules; no old rule text is overwritten.
    for old in previous["attachments"]:
        url = old["url"]
        try:
            if url not in discovered:
                raise ValueError("Current pages changed attachment link; fresh full review required")
            data, receipt = fetch(url)
            receipt["same_as_prior_full_review"] = receipt["bytes"] == old["bytes"] and receipt["sha256"] == old["sha256"]
            attachments.append(receipt)
            if not receipt["same_as_prior_full_review"]:
                with (REPORT / "primary_metadata_01" / ("changed_attachment_" + str(len(attachments)) + ".pdf")).open("xb") as stream:
                    stream.write(data)
        except Exception as exc:
            failures.append(dict(stage="attachment", url=url, error=repr(exc)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(repo_metadata, repo): repo for repo in REPOS}
        for future in concurrent.futures.as_completed(jobs):
            try:
                repos.append(future.result())
            except Exception as exc:
                failures.append(dict(stage="repo", repo=jobs[future], error=repr(exc)))
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), checked_date="2026-10-13",
                  pages=pages, attachments=attachments, repo_metadata=repos, failures=failures,
                  official_attachments_unchanged=len(attachments) == 3 and all(a["same_as_prior_full_review"] for a in attachments),
                  official_catalog_supplement_review="Manual primary-page review: no new video-track supplement found",
                  search_backend_failure="Exa free MCP rate limit; used primary-site Jina reading and GitHub CLI, with web search fallback",
                  media_downloads=0, model_downloads=0, new_model_calls=0)
    save(target, result)
    print(json.dumps(dict(official_attachments_unchanged=result["official_attachments_unchanged"],
                          repos=len(repos), failures=failures, media_downloads=0), ensure_ascii=False))


if __name__ == "__main__":
    main()
