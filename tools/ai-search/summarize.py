#!/usr/bin/env python3
"""Summarize recorded observations, never call models or generate observations."""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
PROMPTS = {p['id']: p for p in json.loads((HERE/'prompts.json').read_text())}
ENGINES = {'chatgpt_search', 'google_ai_mode', 'google_ai_overviews', 'bing_copilot', 'perplexity_search'}
CORRECTNESS = {'correct', 'incorrect', 'not_reviewed', 'not_applicable'}


def mentioned(text):
    return bool(re.search(r'(?<![a-z0-9])rally[\s-]?only(?![a-z0-9])', text, re.I))


def official_url(url):
    p = urlparse(url)
    if p.scheme not in ('https', 'http'):
        return False
    host = (p.hostname or '').lower()
    return (host == 'rallyonly.app' or
            (host == 'yudaliuab-crypto.github.io' and (p.path == '/rallyonly' or p.path.startswith('/rallyonly/'))) or
            (host == 'apps.apple.com' and bool(re.search(r'/id6813940884(?:/|$)', p.path))))


def validate(row):
    for name in ('round_id', 'captured_at', 'prompt_id', 'engine', 'model', 'region', 'ui_language', 'evidence'):
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise ValueError('Missing '+name)
    date = datetime.fromisoformat(row['captured_at'].replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('captured_at must include a timezone')
    if row['prompt_id'] not in PROMPTS or row['engine'] not in ENGINES:
        raise ValueError('Unknown prompt or engine')
    if row.get('trial') not in (1, 2, 3):
        raise ValueError('trial must be 1, 2 or 3')
    if type(row.get('new_conversation')) is not bool or row.get('personalization') not in ('off', 'on', 'unknown'):
        raise ValueError('Record conversation and personalization state')
    if row.get('search_enabled') not in (True, False, None):
        raise ValueError('search_enabled must be true/false/null')
    if row.get('outcome') not in ('answer', 'no_ai_answer', 'blocked'):
        raise ValueError('Unknown outcome')
    if row['outcome'] == 'answer' and not row.get('response_text', '').strip():
        raise ValueError('An answer needs its actual text')
    if type(row.get('citations_reviewed')) is not bool or not isinstance(row.get('citations'), list):
        raise ValueError('Record citation review status and list')
    for citation in row['citations']:
        if not isinstance(citation, dict) or not isinstance(citation.get('url'), str) or type(citation.get('verified')) is not bool:
            raise ValueError('Citations need a URL and explicit verification boolean')
    if row.get('correctness') not in CORRECTNESS:
        raise ValueError('Record correctness review status')
    has_mention = mentioned(row.get('response_text', ''))
    if row['correctness'] in ('correct', 'incorrect') and (row['outcome'] != 'answer' or not has_mention):
        raise ValueError('Only a mentioned brand can have reviewed correctness')
    if row['correctness'] == 'incorrect' and not row.get('correctness_notes', '').strip():
        raise ValueError('Explain the incorrect claim')
    return row


def key(row):
    return tuple(row.get(k) for k in ('round_id', 'engine', 'model', 'region', 'ui_language', 'personalization', 'prompt_id', 'trial'))


def rate(n, d):
    return {'numerator': n, 'denominator': d, 'rate': round(n/d, 4) if d else None}


def summarize(rows):
    seen, groups = set(), defaultdict(list)
    for row in rows:
        validate(row)
        k = key(row)
        if k in seen:
            raise ValueError('Duplicate observation: '+repr(k))
        seen.add(k)
        # Never merge engines, modes, models, regions, languages or rounds silently.
        conditions = tuple(row.get(x) for x in ('round_id', 'engine', 'model', 'region', 'ui_language', 'personalization')) + (PROMPTS[row['prompt_id']]['language'],)
        groups[conditions].append(row)
    output = []
    for conditions, rs in sorted(groups.items()):
        eligible = [r for r in rs if r['outcome'] == 'answer' and r['new_conversation'] and r['personalization'] == 'off' and r.get('search_enabled') is True]
        mentions = [r for r in eligible if mentioned(r['response_text'])]
        reviewed = [r for r in eligible if r['citations_reviewed']]
        cited = [r for r in reviewed if any(c['verified'] and official_url(c['url']) for c in r['citations'])]
        correct_reviewed = [r for r in mentions if r['correctness'] in ('correct', 'incorrect')]
        output.append({
            'conditions': dict(zip(('round_id', 'engine', 'model', 'region', 'ui_language', 'personalization', 'prompt_language'), conditions)),
            'observations': len(rs), 'eligible_answers': len(eligible),
            'no_ai_answer': sum(r['outcome'] == 'no_ai_answer' for r in rs),
            'blocked': sum(r['outcome'] == 'blocked' for r in rs),
            'excluded_answers': sum(r['outcome'] == 'answer' for r in rs)-len(eligible),
            'mention_rate': rate(len(mentions), len(eligible)),
            'citation_rate': rate(len(cited), len(reviewed)),
            'citations_not_reviewed': len(eligible)-len(reviewed),
            'correctness': rate(sum(r['correctness'] == 'correct' for r in correct_reviewed), len(correct_reviewed)),
            'mentioned_answers_not_reviewed': len(mentions)-len(correct_reviewed)})
    return {'groups': output, 'observations': len(rows), 'note': 'Observational sample, not stable ranking or proof of causal lift. Null is unknown, not zero.'}


def traffic(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    result = []
    for row in rows:
        parsed = {k: row.get(k, '') for k in ('date', 'source', 'landing_page', 'campaign', 'attribution_level', 'evidence')}
        for k in ('visits', 'app_store_clicks', 'attributed_downloads'):
            value = row.get(k, '').strip()
            parsed[k] = int(value) if value else None
            if parsed[k] is not None and parsed[k] < 0:
                raise ValueError('Negative '+k)
        result.append(parsed)
    return {'rows': result, 'note': 'No cross-source deduplication or attribution is inferred. A page campaign is not proof of an AI origin. Blank cells remain null.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('observations', type=Path)
    p.add_argument('--traffic', type=Path)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    try:
        rows = [json.loads(line) for line in args.observations.read_text().splitlines() if line.strip()]
        report = summarize(rows)
        if args.traffic:
            report['referrals_downloads'] = traffic(args.traffic)
    except (ValueError, KeyError, TypeError) as e:
        p.error(str(e))
    text = json.dumps(report, ensure_ascii=False, indent=2)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end='')
