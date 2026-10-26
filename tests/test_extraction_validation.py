import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_hn_extraction import align_evidence, validate


class ValidationTests(unittest.TestCase):
    def result(self):
        return {'response': {'is_hiring_ad': True, 'skills': ['Python'], 'salary': [],
                             'seniority': [], 'country': [], 'remote_policy': 'not_stated'}}

    def test_alignment_preserves_raw(self):
        original = self.result()
        original['response']['remote_evidence'] = 'ON SITE'
        normalized, changes = align_evidence(original, 'Role | ONSITE | Python; no non-onsite option')
        self.assertEqual(normalized['response']['remote_evidence'], 'ONSITE')
        self.assertEqual(original['response']['remote_evidence'], 'ON SITE')
        self.assertEqual(len(changes), 1)

    def test_alignment_does_not_invent_evidence(self):
        original = self.result()
        original['response']['remote_evidence'] = 'Worldwide remote'
        normalized, changes = align_evidence(original, 'REMOTE (US only)')
        self.assertEqual(changes, [])
        self.assertIn('unsupported_remote_evidence', validate(normalized, 'REMOTE (US only)'))

    def test_country_requires_explicit_support(self):
        result = self.result()
        result['response'].update(country=['United States'], country_evidence='San Francisco')
        self.assertIn('country_not_explicit:United States', validate(result, 'San Francisco | Python'))
        result['response']['country_evidence'] = 'US'
        self.assertEqual(validate(result, 'US | Python'), [])

    def test_pronoun_is_not_country_abbreviation(self):
        result = self.result()
        result['response'].update(country=['United States'], country_evidence='us')
        self.assertIn('country_not_explicit:United States', validate(result, 'Join us'))

    def test_bad_salary_bounds_are_flagged(self):
        result = self.result()
        result['response']['salary'] = [{'raw_text':'100-50','minimum':100,'maximum':50,'period':'year'}]
        self.assertIn('inverted_salary_range', validate(result, '100-50'))

    def test_inference_failure(self):
        self.assertEqual(validate({'response': None, 'error_message': 'quota'}, ''), ['inference_error_or_invalid_json'])


if __name__ == '__main__':
    unittest.main()
