#!/usr/bin/env python3
"""Dependency-free website invariants; does not claim indexing or rich-result eligibility."""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://rallyonly.app/'
PAGES = ['index.html', 'es/index.html', 'zh/index.html',
         'rallyonly-vs-swingvision.html', 'how-to-automatically-trim-tennis-match-videos.html',
         'how-to-film-tennis-match-iphone.html', 'support.html', 'privacy.html']
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def route(path):
    return path[:-10] if path.endswith('index.html') else path


def norm(text):
    return ' '.join(text.split())


class Node:
    def __init__(self, tag='', attrs=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), []

    def text(self):
        if self.tag in ('script', 'style', 'head'):
            return ''
        return ''.join(c if isinstance(c, str) else c.text() for c in self.children)

    def rawtext(self):
        return ''.join(c if isinstance(c, str) else c.rawtext() for c in self.children)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root, self.nodes = Node(), []
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        self.stack[-1].children.append(text)

    def tags(self, tag):
        return [n for n in self.nodes if n.tag == tag]


def objects(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from objects(v)
    elif isinstance(value, list):
        for v in value:
            yield from objects(v)


def typed(obj, name):
    t = obj.get('@type', [])
    return name in (t if isinstance(t, list) else [t])


def contrast(a, b):
    def luminance(h):
        cs = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]
        cs = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in cs]
        return sum(c*w for c, w in zip(cs, [.2126, .7152, .0722]))
    x, y = sorted([luminance(a), luminance(b)])
    return (y+.05)/(x+.05)


def audit(root=ROOT):
    checks, docs = [], {}

    def check(key, ok, detail=''):
        checks.append({'check': key, 'passed': bool(ok), 'detail': detail})

    titles, descriptions, canonicals = [], [], []
    for name in PAGES:
        path = root/name
        check(name+':exists', path.exists())
        if not path.exists():
            continue
        html = path.read_text(encoding='utf-8')
        doc = docs[name] = Document(html)
        title = [norm(n.rawtext()) for n in doc.tags('title')]
        description = [n.attrs.get('content', '') for n in doc.tags('meta') if n.attrs.get('name') == 'description']
        canonical = [n.attrs.get('href') for n in doc.tags('link') if n.attrs.get('rel') == 'canonical']
        expected = DOMAIN+route(name)
        check(name+':title', len(title) == 1 and bool(title[0]))
        check(name+':description', len(description) == 1 and bool(description[0]))
        check(name+':canonical', canonical == [expected], repr(canonical))
        titles += title; descriptions += description; canonicals += canonical
        check(name+':one-h1', len(doc.tags('h1')) == 1)
        check(name+':language', len(doc.tags('html')) == 1 and doc.tags('html')[0].attrs.get('lang') == ('es' if name.startswith('es/') else 'zh-Hans' if name.startswith('zh/') else 'en'))
        check(name+':server-rendered-text', len(norm(doc.root.text())) > 400)
        robot_meta = ' '.join(n.attrs.get('content', '') for n in doc.tags('meta') if n.attrs.get('name', '').lower() in ('robots', 'googlebot', 'bingbot')).lower()
        check(name+':indexable-directives', not any(v in robot_meta for v in ('noindex', 'nosnippet', 'max-snippet:0')))
        ids = [n.attrs['id'] for n in doc.nodes if 'id' in n.attrs]
        check(name+':unique-ids', len(ids) == len(set(ids)))
        check(name+':skip-link', any(n.attrs.get('href') == '#main' for n in doc.tags('a')) and 'main' in ids)
        check(name+':image-alt', all('alt' in n.attrs for n in doc.tags('img')))
        all_json = []
        for i, n in enumerate(doc.tags('script')):
            if n.attrs.get('type') != 'application/ld+json':
                continue
            try:
                all_json += list(objects(json.loads(n.rawtext())))
                check(name+f':jsonld-{i}', True)
            except ValueError as e:
                check(name+f':jsonld-{i}', False, str(e))
        # FAQ statements must be visible, not just hidden instructions for a crawler.
        visible = norm(doc.root.text())
        for faq in [o for o in all_json if typed(o, 'FAQPage')]:
            for q in faq.get('mainEntity', []):
                check(name+':visible-faq:'+q.get('name', ''), norm(q.get('name', '')) in visible and norm(q.get('acceptedAnswer', {}).get('text', '')) in visible)
        if name in ('index.html', 'es/index.html', 'zh/index.html'):
            apps = [o for o in all_json if typed(o, 'MobileApplication') or typed(o, 'SoftwareApplication')]
            check(name+':one-app-entity', len(apps) == 1)
            if apps:
                app = apps[0]
                check(name+':iphone-only-schema', app.get('availableOnDevice') == 'iPhone' and '17' in app.get('operatingSystem', ''))
                check(name+':no-invented-reviews', not any(k in app for k in ('aggregateRating', 'review')))
                offer = app.get('offers', {})
                check(name+':qualified-free-offer', str(offer.get('price')) in ('0', '0.0') and bool(offer.get('description')) and '4' in offer.get('description', ''))
                check(name+':app-identity', app.get('@id') == DOMAIN+'#app' and '6813940884' in app.get('installUrl', ''))
        for table in doc.tags('table'):
            descendants = []
            def walk(n):
                for c in n.children:
                    if isinstance(c, Node):
                        descendants.append(c); walk(c)
            walk(table)
            check(name+':table-caption', any(n.tag == 'caption' for n in descendants))
            check(name+':table-header-scope', all(n.attrs.get('scope') in ('col', 'row') for n in descendants if n.tag == 'th'))

    check('unique-titles', len(titles) == len(set(titles)))
    check('unique-descriptions', len(descriptions) == len(set(descriptions)))
    check('unique-canonicals', len(canonicals) == len(set(canonicals)))
    alternate_set = {'en': DOMAIN, 'es': DOMAIN+'es/', 'zh-Hans': DOMAIN+'zh/', 'x-default': DOMAIN}
    for name in ('index.html', 'es/index.html', 'zh/index.html'):
        if name in docs:
            alts = {n.attrs.get('hreflang'): n.attrs.get('href') for n in docs[name].tags('link') if n.attrs.get('rel') == 'alternate'}
            check(name+':reciprocal-home-alternates', alts == alternate_set, repr(alts))

    graph = {name: set() for name in docs}
    for name, doc in docs.items():
        # Relative asset/navigation links must resolve both at the custom-domain root and
        # under a GitHub Pages project prefix. Canonicals intentionally stay absolute.
        for prefix in ('/', '/rallyonly/'):
            origin = 'https://preview.invalid'+prefix+route(name)
            for node in doc.nodes:
                attr = 'href' if node.tag in ('a', 'link') else 'src' if node.tag in ('img', 'script', 'source', 'video') else None
                val = node.attrs.get(attr, '') if attr else ''
                if not val or val.startswith(('mailto:', 'tel:', 'data:')):
                    continue
                parsed = urlparse(urljoin(origin, val))
                if parsed.netloc == 'rallyonly.app':
                    relative = parsed.path.lstrip('/')
                elif parsed.netloc == 'preview.invalid' and parsed.path.startswith(prefix):
                    relative = parsed.path[len(prefix):]
                elif parsed.netloc == 'preview.invalid':
                    check(name+':project-prefix:'+val, False)
                    continue
                else:
                    continue
                relative = unquote(relative)
                target = root/relative
                if target.is_dir(): target /= 'index.html'
                check(name+':local-link:'+prefix+val, target.is_file(), str(target.relative_to(root)))
                if target.is_file() and target.suffix == '.html' and target.relative_to(root).as_posix() in docs:
                    dest = target.relative_to(root).as_posix()
                    if node.tag == 'a': graph[name].add(dest)
                    if parsed.fragment:
                        check(name+':anchor:'+val, any(n.attrs.get('id') == parsed.fragment for n in docs[dest].nodes))
    reachable, pending = set(), ['index.html']
    while pending:
        n = pending.pop()
        if n not in reachable:
            reachable.add(n); pending += list(graph.get(n, set())-reachable)
    check('all-public-pages-reachable', set(PAGES) <= reachable, repr(sorted(set(PAGES)-reachable)))
    try:
        xml = ET.fromstring((root/'sitemap.xml').read_text())
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locs = [n.text for n in xml.findall('s:url/s:loc', ns)]
        check('sitemap-canonical-pages', set(locs) == {DOMAIN+route(n) for n in PAGES} and len(locs) == len(set(locs)))
        for date in xml.findall('s:url/s:lastmod', ns):
            check('sitemap-date-format', bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', date.text or '')))
    except (ValueError, ET.ParseError) as e:
        check('sitemap-xml', False, str(e))
    robots = RobotFileParser()
    robots.parse((root/'robots.txt').read_text().splitlines())
    for agent in ('OAI-SearchBot', 'Googlebot', 'bingbot'):
        check('robots-allows:'+agent, all(robots.can_fetch(agent, DOMAIN+route(n)) for n in PAGES))
    check('robots-sitemap', DOMAIN+'sitemap.xml' in (robots.site_maps() or []))
    check('custom-domain-preserved', (root/'CNAME').read_text().strip() == 'rallyonly.app')
    css = (root/'site.css').read_text()
    dark = re.search(r'@media \(prefers-color-scheme: dark\).*?--brand:(#[0-9a-fA-F]{6})', css, re.S)
    if dark:
        ratio = contrast(dark[1], '#0c1110')
        check('dark-link-contrast', ratio >= 4.5, f'{ratio:.2f}:1 (normal text minimum 4.5:1)')
    return {'checks': checks, 'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
            'not_proven': ['Actual indexing', 'Google-selected canonical', 'Verified crawler IP access', 'AI citations', 'Google rich-result eligibility', 'Owner-tool verification/submissions']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    for c in result['checks']:
        if not c['passed']:
            print('FAIL', c['check'], c['detail'])
    print(f"{result['passed']} passed; {result['failed']} failed. Local invariants only.")
    raise SystemExit(bool(result['failed']))
