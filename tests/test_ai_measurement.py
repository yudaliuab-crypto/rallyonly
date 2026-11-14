import importlib.util
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('summary', ROOT/'tools/ai-search/summarize.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def record(**kwargs):
    row = dict(round_id='SYNTHETIC-UNIT-TEST', captured_at='2026-11-15T12:00:00+01:00',
               prompt_id='Q01', engine='chatgpt_search', model='test fixture', region='ES',
               ui_language='en', trial=1, new_conversation=True, personalization='off', search_enabled=True,
               outcome='answer', response_text='A synthetic answer mentioning RallyOnly.',
               citations_reviewed=True, citations=[], correctness='not_reviewed', evidence='synthetic-test-only.txt')
    row.update(kwargs)
    return row


class MeasurementTest(unittest.TestCase):
    def test_mentions_chinese_boundaries_and_negative_statement(self):
        self.assertTrue(m.mentioned('推荐RallyOnly，支持本地处理。'))
        self.assertTrue(m.mentioned('I would not recommend RallyOnly.'))
        self.assertTrue(m.mentioned('Try Rally Only'))
        self.assertFalse(m.mentioned('AnotherRallyOnlyClone'))

    def test_official_citation_identity_not_lookalikes(self):
        for url in ['https://rallyonly.app/es/', 'https://yudaliuab-crypto.github.io/rallyonly/support.html',
                    'https://apps.apple.com/us/app/name/id6813940884?utm_source=chatgpt.com']:
            self.assertTrue(m.official_url(url))
        for url in ['https://rallyonly.app.evil.invalid/', 'https://apps.apple.com/us/app/id989461317',
                    'https://yudaliuab-crypto.github.io/other/', 'https://evil.invalid/?rallyonly.app']:
            self.assertFalse(m.official_url(url))

    def test_unknowns_excluded_and_no_ai_answer_not_negative(self):
        rows = [record(), record(trial=2, outcome='no_ai_answer', response_text=''),
                record(trial=3, search_enabled=None)]
        g = m.summarize(rows)['groups'][0]
        self.assertEqual(g['eligible_answers'], 1)
        self.assertEqual(g['mention_rate']['rate'], 1)
        self.assertEqual(g['no_ai_answer'], 1)
        self.assertEqual(g['excluded_answers'], 1)
        self.assertIsNone(g['correctness']['rate'])

    def test_citation_verification_and_review_denominator(self):
        rows = [record(citations=[{'url':'https://rallyonly.app/', 'verified':True}]),
                record(trial=2, citations=[{'url':'https://rallyonly.app/', 'verified':False}]),
                record(trial=3, citations_reviewed=False)]
        g = m.summarize(rows)['groups'][0]
        self.assertEqual(g['citation_rate'], {'numerator':1, 'denominator':2, 'rate':.5})
        self.assertEqual(g['citations_not_reviewed'], 1)

    def test_duplicate_observations_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            m.summarize([record(), deepcopy(record())])

    def test_conditions_are_not_silently_pooled(self):
        rows = [record(), record(engine='google_ai_mode'), record(prompt_id='Q08')]
        self.assertEqual(len(m.summarize(rows)['groups']), 3)

    def test_incorrect_claim_needs_review_evidence(self):
        with self.assertRaisesRegex(ValueError, 'Explain'):
            m.summarize([record(correctness='incorrect')])
        g = m.summarize([record(correctness='incorrect', correctness_notes='Fixture says Android; current product is iPhone only.')])['groups'][0]
        self.assertEqual(g['correctness']['rate'], 0)

    def test_blank_downloads_stay_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'traffic.csv'
            p.write_text('date,source,landing_page,campaign,visits,app_store_clicks,attributed_downloads,attribution_level,evidence\n2026-11-15,fixture,/,fixture,2,,,page_campaign_only,fixture.txt\n')
            row = m.traffic(p)['rows'][0]
            self.assertEqual(row['visits'], 2)
            self.assertIsNone(row['attributed_downloads'])

    def test_empty_sample_has_no_rates(self):
        self.assertEqual(m.summarize([])['groups'], [])


if __name__ == '__main__':
    unittest.main()
