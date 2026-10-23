"""One current direct primary-page read; unchanged PDFs are not fetched again."""
from datetime import datetime, timezone

from t_io import ROOT, check, fetch, identity, read, save


def review():
    folder = ROOT / 'official_freshness122'; folder.mkdir()
    prior_path = ROOT / 'official_rules23_before_native101/completion.json'
    prior = read(prior_path); pages = {}; changed = []
    for name, item in prior['pages'].items():
        check(item['source'])
        pages[name] = fetch(item['url'], folder / (name + '.html'), 524288)
        if pages[name]['source']['sha256'] != item['source']['sha256']:
            changed.append(name)
    save(folder / 'completion.json', dict(state='PRIMARY_CURRENT_HTML_EXACTLY_UNCHANGED' if not changed
        else 'PRIMARY_PAGE_CHANGED_REQUIRES_READING_BEFORE_MODEL', checked_UTC=datetime.now(timezone.utc).isoformat(),
        pages=pages, changed_pages=changed, original_full_rule_read=identity(prior_path),
        PDFs_not_downloaded_again=True, unchanged_prior_rules_and_links_adopted=not changed,
        no_special_organizer_permission_claim=True))
    if changed:
        raise RuntimeError('Primary page changed; preserve fresh bytes and review before inference')
    return identity(folder / 'completion.json')
