"""Source-grounded checks shared by benchmarking and archive processing."""
import copy
import re

EVIDENCE_FIELDS = ['seniority_evidence', 'remote_evidence', 'remote_restrictions', 'country_evidence', 'location_text']
SENIORITY = {'intern', 'student', 'junior', 'mid', 'senior', 'lead', 'staff', 'principal', 'manager', 'director', 'head', 'chief', 'executive', 'experienced_unspecified'}


def align_evidence(result, text):
    result = copy.deepcopy(result)
    data = result.get('response')
    changes = []
    if not isinstance(data, dict):
        return result, changes
    fields = [(data, field) for field in EVIDENCE_FIELDS]
    fields += [(salary, 'raw_text') for salary in data.get('salary') or [] if isinstance(salary, dict)]
    for obj, key in fields:
        quote = obj.get(key)
        if not isinstance(quote, str) or not quote or quote in text:
            continue
        pattern = r'\s*'.join(re.escape(c) for c in quote if not c.isspace())
        if not pattern:
            continue
        matches = {m.group() for m in re.finditer(pattern, text)}
        if not matches:
            matches = {m.group() for m in re.finditer(pattern, text, re.IGNORECASE)}
        if len(matches) == 1:
            replacement = matches.pop()
            obj[key] = replacement
            changes.append({'field': key, 'model_text': quote, 'source_text': replacement})
    return result, changes


def validate(result, text):
    issues = []
    data = result.get('response')
    if result.get('error_message') or not isinstance(data, dict):
        return ['inference_error_or_invalid_json']
    if not isinstance(data.get('is_hiring_ad'), bool):
        issues.append('invalid_hiring_flag')
    for field in ['skills', 'seniority', 'country', 'salary']:
        if not isinstance(data.get(field), list):
            issues.append('invalid_' + field)
    if issues:
        return issues
    if any(not isinstance(v, str) for field in ['skills', 'seniority', 'country'] for v in data[field]):
        return ['invalid_array_member']
    if data.get('remote_policy') not in {'remote', 'hybrid', 'onsite', 'mixed', 'not_stated'}:
        issues.append('invalid_remote_policy')
    if not set(data['seniority']).issubset(SENIORITY):
        issues.append('invalid_seniority_label')
    for field in EVIDENCE_FIELDS:
        quote = data.get(field)
        if quote is not None and (not isinstance(quote, str) or quote not in text):
            issues.append('unsupported_' + field)
    if data['seniority'] and not data.get('seniority_evidence'):
        issues.append('missing_seniority_evidence')
    if data['country'] and not data.get('country_evidence'):
        issues.append('missing_country_evidence')
    if data.get('remote_policy') != 'not_stated' and not data.get('remote_evidence'):
        issues.append('missing_remote_evidence')
    country_aliases = {'United States': ['USA', 'US', 'U.S.', 'U.S.A.'],
                       'United States of America': ['USA', 'US', 'U.S.', 'U.S.A.'],
                       'United Kingdom': ['UK', 'U.K.'], 'United Arab Emirates': ['UAE'],
                       'South Korea': ['Republic of Korea'], 'Czechia': ['Czech Republic']}
    for country in data['country']:
        explicit = re.search(r'(?<!\w)' + re.escape(country) + r'(?!\w)', text, re.I)
        aliases = country_aliases.get(country, [])
        if not explicit and not any(re.search(r'(?<!\w)' + re.escape(a) + r'(?!\w)', text) for a in aliases):
            issues.append('country_not_explicit:' + country)
    for salary in data['salary']:
        if not isinstance(salary, dict):
            issues.append('invalid_salary')
            continue
        quote = salary.get('raw_text')
        if not isinstance(quote, str) or not quote or quote not in text:
            issues.append('unsupported_salary_quote')
        low, high = salary.get('minimum'), salary.get('maximum')
        for value in [low, high]:
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
                issues.append('invalid_salary_amount')
        if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > high:
            issues.append('inverted_salary_range')
        if salary.get('period') not in {'hour', 'day', 'week', 'month', 'year', 'not_stated'}:
            issues.append('invalid_salary_period')
    if data.get('is_hiring_ad') is False and any(data[field] for field in ['skills', 'salary', 'seniority', 'country']):
        issues.append('non_hiring_post_has_job_facts')
    return sorted(set(issues))
