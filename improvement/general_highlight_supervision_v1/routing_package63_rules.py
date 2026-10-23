"""Bounded current public HTML check; reuse historical full PDF review honestly."""
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin
from datetime import datetime, timezone
from common import fetch
from routing_package63_common import ROOT, read, ref, save


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.current = None; self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = dict(href=dict(attrs).get('href', ''), text='')

    def handle_data(self, text):
        self.text.append(text)
        if self.current is not None:
            self.current['text'] += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current); self.current = None


def check_current_rules():
    urls = dict(main='https://www.aicomp.cn/tracks/tracks-6/4267.html',
        notice='https://www.aicomp.cn/notice/notice-3/5307.html',
        catalog='https://www.aicomp.cn/notice/notice-3/')
    pages = {}; links = {}; visible = {}
    for name, url in urls.items():
        path = ROOT / ('official_' + name + '.html')
        pages[name] = fetch(url, path, 1 << 20)
        text = path.read_text(encoding='utf-8')
        parser = Links(); parser.feed(text); links[name] = parser.links
        visible[name] = ''.join(''.join(parser.text).split())
    notice_pdfs = {unquote(urljoin(urls['notice'], item['href'])) for item in links['notice']
                   if '.pdf' in item['href'].lower()}
    prior = read(ROOT.parent / 'code/prior_attachment_review63.json')
    expected = {unquote(item['url']) for item in prior['attachments']}
    if notice_pdfs != expected:
        raise ValueError('Current notice attachment URLs changed; review new scope before packaging')
    relevant = [dict(url=urljoin(urls['catalog'], item['href']), title=item['text'].strip())
        for item in links['catalog'] if '视频' in item['text'] and '高光' in item['text']]
    if any(not item['url'].rstrip('/').endswith('/5307.html') for item in relevant):
        raise ValueError('Another relevant video notice requires review before packaging')
    main = visible['main']
    if not all(phrase in main for phrase in ['不得超过9B', '空predictions', '反向构造规则']):
        raise ValueError('Current main-body constraints differ from reviewed scope')
    save(ROOT / 'official_rule_check_before_package.json', dict(
        checked_UTC=datetime.now(timezone.utc).isoformat(), pages=pages,
        current_notice_PDF_URLs=sorted(notice_pdfs), current_relevant_catalog=relevant,
        prior_full_PDF_review=ref(ROOT.parent / 'code/prior_attachment_review63.json'),
        PDFs_not_downloaded_again=True, current_PDF_bytes_not_independently_rechecked=True,
        interpretation='Public external training plus automatic frozen semantic routing is within stated scope; legal data, reproducibility, no test labels/manual edits/reverse rules, all models<=9B remain required. Not organizer-specific approval.',
        automatic_website_submission=False, actual_all_parameters=8816809946))
