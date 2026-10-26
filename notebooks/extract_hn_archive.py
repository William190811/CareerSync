# Databricks notebook source
"""Resumable archive extraction on serverless compute; no schedule or paid fallback."""
import datetime as dt
import json
import sys

sys.path.insert(0, '/Workspace/Shared/tech_careers')
from validate_hn_extraction import align_evidence, validate


def run(spark):
    config = json.load(open('/Volumes/workspace/tech_careers/ingestion/extraction_config.json', encoding='utf-8'))
    model, prompt_hash = config['model'], config['prompt_hash']
    base = 'workspace.tech_careers'
    inputs = base + '.hn_extraction_inputs'
    raw = base + '.hn_extraction_inferences'
    final = base + '.hn_extraction_validated'

    def lit(value):
        return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"

    def execute(statement):
        return spark.sql(statement).collect()

    execute(f'''CREATE TABLE IF NOT EXISTS {inputs} USING DELTA AS
        SELECT item_id, sha2(text_plain,256) input_hash, month, created_at_unix, text_plain,
               source_url, unavailable FROM {base}.hn_raw_posts''')
    execute(f'''CREATE TABLE IF NOT EXISTS {raw} (
        item_id BIGINT, input_hash STRING, model STRING, prompt_hash STRING,
        extracted_at TIMESTAMP, ai_result VARIANT) USING DELTA''')
    execute(f'''CREATE TABLE IF NOT EXISTS {final} (
        item_id BIGINT, input_hash STRING, model STRING, prompt_hash STRING,
        processed_at TIMESTAMP, extraction_status STRING, normalized_json STRING,
        validation_issues ARRAY<STRING>, evidence_alignments_json STRING) USING DELTA''')
    key = f"model={lit(model)} AND prompt_hash={lit(prompt_hash)}"
    # Seed exactly this prompt/model's benchmark outputs, not another candidate's answers.
    execute(f'''INSERT INTO {raw}
        SELECT b.item_id, s.input_hash, b.model, b.prompt_hash, b.tested_at, b.ai_result
        FROM {base}.hn_model_benchmark b JOIN {inputs} s ON b.item_id=s.item_id
        LEFT ANTI JOIN {raw} r ON r.item_id=b.item_id AND r.input_hash=s.input_hash
            AND r.model=b.model AND r.prompt_hash=b.prompt_hash
        WHERE b.model={lit(model)} AND b.prompt_hash={lit(prompt_hash)}''')
    execute(f'''INSERT INTO {raw}
        SELECT s.item_id, s.input_hash, {lit(model)}, {lit(prompt_hash)}, current_timestamp(),
            parse_json('{{"response":null,"error_message":"Source text unavailable"}}')
        FROM {inputs} s LEFT ANTI JOIN {raw} r ON s.item_id=r.item_id
            AND s.input_hash=r.input_hash AND r.model={lit(model)} AND r.prompt_hash={lit(prompt_hash)}
        WHERE s.unavailable OR trim(s.text_plain)='' ''')

    def validate_pending():
        candidates = spark.sql(f'''SELECT r.item_id, r.input_hash, to_json(r.ai_result) result_json,
                s.text_plain, s.unavailable FROM {raw} r JOIN {inputs} s
                ON r.item_id=s.item_id AND r.input_hash=s.input_hash
            LEFT ANTI JOIN {final} f ON f.item_id=r.item_id AND f.input_hash=r.input_hash
                AND f.model=r.model AND f.prompt_hash=r.prompt_hash
            WHERE r.model={lit(model)} AND r.prompt_hash={lit(prompt_hash)}''').collect()
        records = []
        failures = 0
        for row in candidates:
            result = json.loads(row.result_json) if row.result_json else {'response': None}
            normalized, changes = align_evidence(result, row.text_plain)
            issues = [] if row.unavailable else validate(normalized, row.text_plain)
            data = normalized.get('response')
            if row.unavailable:
                status = 'skipped_unavailable'
            elif not isinstance(data, dict) or result.get('error_message'):
                status = 'failed'
                failures += 1
            elif issues:
                status = 'needs_review'
            elif not data.get('is_hiring_ad'):
                status = 'non_hiring'
            else:
                status = 'ready'
            records.append((row.item_id, row.input_hash, model, prompt_hash,
                            dt.datetime.now(dt.timezone.utc).replace(tzinfo=None), status,
                            json.dumps(normalized, ensure_ascii=False), issues, json.dumps(changes)))
        if records:
            schema = 'item_id LONG,input_hash STRING,model STRING,prompt_hash STRING,processed_at TIMESTAMP,extraction_status STRING,normalized_json STRING,validation_issues ARRAY<STRING>,evidence_alignments_json STRING'
            spark.createDataFrame(records, schema).write.mode('append').saveAsTable(final)
        return failures, len(records)

    validate_pending()
    # View definition is generated from the same field contract used in the pilot.
    execute(config['view_sql'])
    total = spark.table(inputs).count()
    while True:
        source = f'''SELECT s.* FROM {inputs} s LEFT ANTI JOIN {raw} r
            ON s.item_id=r.item_id AND s.input_hash=r.input_hash
                AND r.model={lit(model)} AND r.prompt_hash={lit(prompt_hash)}
            WHERE NOT s.unavailable AND trim(s.text_plain)<>''
            ORDER BY s.created_at_unix, s.item_id LIMIT 500'''
        remaining = spark.sql(source).count()
        if remaining == 0:
            break
        parallel_source = f'SELECT /*+ REPARTITION(32) */ * FROM ({source})'
        model_sql = config['model_sql'].replace('__SOURCE__', parallel_source)
        execute(f'''INSERT INTO {raw}
            SELECT item_id, input_hash, {lit(model)}, {lit(prompt_hash)}, current_timestamp(), ai_result
            FROM ({model_sql})''')
        failures, processed = validate_pending()
        done = spark.sql(f'SELECT COUNT(*) n FROM {final} WHERE {key}').first().n
        print(json.dumps({'processed': done, 'total': total, 'last_batch': processed, 'inference_failures': failures}), flush=True)
        if processed and failures / processed >= 0.5:
            raise RuntimeError('At least half the batch failed inference. Stopped to preserve quota; inspect error records before resuming.')
    counts = [row.asDict() for row in spark.sql(f'''SELECT extraction_status, COUNT(*) n
        FROM {final} WHERE {key} GROUP BY extraction_status''').collect()]
    stored = spark.sql(f'SELECT COUNT(*) n, COUNT(DISTINCT item_id) unique_n FROM {final} WHERE {key}').first()
    if stored.n != total or stored.unique_n != total:
        raise RuntimeError(f'Coverage mismatch: {stored} versus {total}')
    print(json.dumps({'complete': True, 'model': model, 'total': total, 'statuses': counts}), flush=True)


if 'spark' in globals():
    run(spark)
