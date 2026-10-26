"""Compare workspace models on the same reviewed 20-post sample."""
import hashlib
import json
import time
import copy

import extract_hn_sample as pilot
import ingest_hn as hn
from validate_hn_extraction import align_evidence

MODELS = ['system.ai.gpt-oss-120b', 'system.ai.qwen3-next-80b-a3b-instruct',
          'system.ai.meta-llama-3-3-70b-instruct', 'ai_extract_precision',
          'system.ai.gpt-oss-20b', 'system.ai.qwen35-122b-a10b']
PROMPT = pilot.INSTRUCTIONS + '\nReturn only a JSON object with these fields and types:\n' + json.dumps(pilot.SCHEMA) + '\nPOST TO EXTRACT:\n'
PROMPT_HASH = hashlib.sha256(PROMPT.encode()).hexdigest()
TABLE = f'{hn.BASE}.hn_model_benchmark'


def expression(model, text='text_plain'):
    if model == 'ai_extract_precision':
        return f"ai_extract({text}, {pilot.literal(json.dumps(pilot.SCHEMA))}, map('version','2.0','mode','precision','instructions',{pilot.literal(pilot.INSTRUCTIONS)}))"
    return f'''parse_json(to_json(named_struct(
        'response', try_parse_json(inference.result),
        'error_message', inference.errorMessage)))'''


def model_sql(model, source):
    if model == 'ai_extract_precision':
        return f'SELECT *, {expression(model)} AS ai_result FROM ({source})'
    return f'''SELECT *, {expression(model)} AS ai_result FROM (
        SELECT *, ai_query({pilot.literal(model)}, concat({pilot.literal(PROMPT)}, text_plain),
            failOnError => false, responseFormat => '{{"type":"json_object"}}',
            modelParameters => named_struct('temperature', CAST(0.0 AS DOUBLE), 'max_tokens', 4096)) AS inference
        FROM ({source}))'''


def run():
    pilot.query(f'''CREATE TABLE IF NOT EXISTS {TABLE} (
        model STRING, prompt_hash STRING, item_id BIGINT, ai_result VARIANT, tested_at TIMESTAMP
    ) USING DELTA''', 'benchmark_create')
    summaries = []
    for model in MODELS:
        started = time.monotonic()
        slug = model.replace('.', '_').replace('-', '_')
        source = f'''SELECT s.* FROM {pilot.INPUT} s LEFT ANTI JOIN {TABLE} r
            ON s.item_id = r.item_id AND r.model = {pilot.literal(model)}
                AND r.prompt_hash = '{PROMPT_HASH}' WHERE NOT s.unavailable'''
        print(f'Testing {model}', flush=True)
        pilot.query(f'''INSERT INTO {TABLE}
            SELECT {pilot.literal(model)}, '{PROMPT_HASH}', item_id, ai_result, current_timestamp()
            FROM ({model_sql(model, source)})''', f'benchmark_{slug}')
        elapsed = time.monotonic() - started
        rows = pilot.query(f'''SELECT s.item_id, s.source_url, s.text_plain,
            CASE WHEN s.unavailable THEN 'skipped_unavailable'
                 WHEN r.ai_result:error_message::STRING IS NOT NULL OR r.ai_result:response IS NULL
                    OR is_variant_null(r.ai_result:response) THEN 'failed' ELSE 'extracted' END AS extraction_status,
            CASE WHEN s.unavailable THEN '{{"response":null,"error_message":"Source text unavailable"}}'
                 ELSE to_json(r.ai_result) END AS result_json
            FROM {pilot.INPUT} s LEFT JOIN {TABLE} r ON s.item_id=r.item_id
                AND r.model={pilot.literal(model)} AND r.prompt_hash='{PROMPT_HASH}'
            ORDER BY s.created_at_unix, s.item_id''', f'benchmark_review_{slug}')
        raw_summary = pilot.evaluate(copy.deepcopy(rows))
        adjustments = 0
        for row in rows:
            result = json.loads(row.pop('result_json'))
            row['result'], row['evidence_alignments'] = align_evidence(result, row['text_plain'])
            adjustments += len(row['evidence_alignments'])
        summary = pilot.evaluate(rows)
        summary['raw_check_failures'] = len(raw_summary['issues'])
        summary['evidence_alignments'] = adjustments
        prior_file = hn.DATA / f'benchmark_{slug}.json'
        if prior_file.exists():
            prior = json.loads(prior_file.read_text(encoding='utf-8'))['summary']
            if prior.get('prompt_hash') == PROMPT_HASH:
                elapsed = prior['elapsed_seconds']
        summary.update(model=model, elapsed_seconds=round(elapsed, 2), prompt_hash=PROMPT_HASH)
        summaries.append(summary)
        (hn.DATA / f'benchmark_{slug}.json').write_text(json.dumps({'summary': summary, 'rows': rows}, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(summary), flush=True)
    summaries.sort(key=lambda s: (18 - s['extracted'], len(s['issues']), s['elapsed_seconds']))
    winner = summaries[0]
    result = {'winner': winner['model'], 'prompt_hash': PROMPT_HASH, 'ranking': summaries}
    (hn.DATA / 'model_selection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Model comparison', '', 'All candidates used the same 18 readable posts, schema, instructions, and reviewed expectations; two unavailable records were retained as skipped.', '',
             '| Candidate | Readable successes | Check failures | SQL inference seconds |', '|---|---:|---:|---:|']
    for s in summaries:
        lines.append(f"| {s['model']} | {s['extracted']}/18 | {len(s['issues'])} | {s['elapsed_seconds']} |")
    lines.extend(['', f"Selected: **{winner['model']}**. Selection prioritizes successful responses, then fewer check failures, then lower elapsed time.", '',
                  'Evidence alignment restores exact source spelling only when characters match apart from whitespace or case, and keeps raw outputs unchanged. Scores above include that same alignment for every candidate.', '',
                  'Timing includes SQL overhead and is not per-request latency or a cost estimate. This is a small, previously tuned January 2020 development sample, not an independent accuracy benchmark. No universal model-quality claim follows from it. ai_extract uses a Databricks-managed model whose identity is not exposed by this test.', ''])
    for s in summaries:
        lines.append('## ' + s['model'])
        lines.extend(['', *(['- ' + issue for issue in s['issues']] or ['No reviewed-check failures.']), ''])
    (hn.ROOT / 'reports/model-comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    if winner['issues']:
        raise RuntimeError('No candidate passed all reviewed checks; inspect before scaling')
    print('SELECTED ' + winner['model'], flush=True)


if __name__ == '__main__':
    run()
