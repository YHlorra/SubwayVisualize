import requests
from typing import List, Dict, Any
from html.parser import HTMLParser
from urllib.parse import urljoin
from ..config import get_firecrawl_settings

class _AnchorParser(HTMLParser):
    def __init__(self, base_url: str = ''):
        super().__init__()
        self.items: List[Dict[str, str]] = []
        self._in_a = False
        self._cur_href = ''
        self._cur_text = ''
        self._base = base_url or ''

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self._in_a = True
            href = ''
            for k, v in attrs:
                if k.lower() == 'href':
                    href = v or ''
                    break
            if href:
                self._cur_href = urljoin(self._base, href)

    def handle_data(self, data):
        if self._in_a:
            self._cur_text += (data or '')

    def handle_endtag(self, tag):
        if tag.lower() == 'a':
            t = (self._cur_text or '').strip()
            h = (self._cur_href or '').strip()
            if h:
                self.items.append({'text': t, 'href': h})
            self._in_a = False
            self._cur_href = ''
            self._cur_text = ''

def firecrawl_enabled() -> bool:
    cfg = get_firecrawl_settings()
    return bool(cfg.get('enabled'))

def collect_anchors_with_firecrawl(url: str) -> List[Dict[str, str]]:
    cfg = get_firecrawl_settings()
    if not cfg.get('enabled'):
        return []
    base = cfg.get('base')
    key = cfg.get('key')
    timeout = cfg.get('timeout') or 30
    api = base.rstrip('/') + '/scrape'
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }
    body: Dict[str, Any] = {
        'url': url,
        'formats': ['html'],
        'onlyMainContent': False,
        'timeout': timeout * 1000,
        'maxAge': 172800000,
    }
    try:
        r = requests.post(api, headers=headers, json=body, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        data = j.get('data') or {}
        html = data.get('html') or ''
        if not html:
            return []
        parser = _AnchorParser(url)
        parser.feed(html)
        return parser.items
    except Exception:
        return []

def probe_list_page(url: str) -> bool:
    cfg = get_firecrawl_settings()
    if not cfg.get('enabled'):
        return False
    base = cfg.get('base')
    key = cfg.get('key')
    timeout = cfg.get('timeout') or 30
    api = base.rstrip('/') + '/scrape'
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }
    body: Dict[str, Any] = {
        'url': url,
        'formats': ['html'],
        'onlyMainContent': False,
        'timeout': timeout * 1000,
        'maxAge': 172800000,
    }
    try:
        r = requests.post(api, headers=headers, json=body, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        data = j.get('data') or {}
        html = (data.get('html') or '').lower()
        if not html:
            return False
        signals = ['zu-itemmod', '租', '元', 'price', '房源', 'list-item']
        return any(s in html for s in signals)
    except Exception:
        return False

def fetch_html_with_firecrawl(url: str) -> str:
    cfg = get_firecrawl_settings()
    if not cfg.get('enabled'):
        return ''
    base = cfg.get('base')
    key = cfg.get('key')
    timeout = cfg.get('timeout') or 30
    api = base.rstrip('/') + '/scrape'
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }
    body: Dict[str, Any] = {
        'url': url,
        'formats': ['html'],
        'onlyMainContent': False,
        'timeout': timeout * 1000,
        'maxAge': 60000,
    }
    try:
        r = requests.post(api, headers=headers, json=body, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        data = j.get('data') or {}
        html = data.get('html') or ''
        return html or ''
    except Exception:
        return ''

def resolve_line_hrefs_with_firecrawl(url: str) -> Dict[int, str]:
    cfg = get_firecrawl_settings()
    if not cfg.get('enabled'):
        return {}
    items = collect_anchors_with_firecrawl(url)
    out: Dict[int, str] = {}
    try:
        for a in items:
            href = (a or {}).get('href') or ''
            text = (a or {}).get('text') or ''
            if ('/ditie/' in href) and (('号线' in text) or ('号线' in href)):
                n = None
                m1 = None
                import re as _re
                m1 = _re.search(r'(\d+)号线', text) or _re.search(r'(\d+)号线', href)
                if m1:
                    n = int(m1.group(1))
                else:
                    for k,v in {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.items():
                        if f'{k}号线' in text:
                            n = v
                            break
                if n:
                    out[n] = href
    except Exception:
        return out
    return out
