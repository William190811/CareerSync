"""Deploy and launch the selected-model archive extraction inside Databricks."""
import json

import benchmark_hn_models as benchmark
import extract_hn_sample as pilot
import ingest_hn as hn


def run():
    run_record = hn.DATA / 'full_extraction_run.json'
    previous = json.loads(run_record.read_text(encoding='utf-8')) if run_record.exists() else None
    if previous:
        current = json.loads(hn.cli('jobs', 'get-run', str(previous['run_id']), '--output', 'json'))
        if current['state']['life_cycle_state'] not in ['TERMINATED', 'SKIPPED', 'INTERNAL_ERROR']:
            raise RuntimeError(f"Archive extraction is already active: run {previous['run_id']}")
    selection = json.loads((hn.DATA / 'model_selection.json').read_text(encoding='utf-8'))
    winner = selection['ranking'][0]
    if winner['issues'] or winner['extracted'] != 18:
        raise RuntimeError('Selected candidate did not pass the reviewed pilot')
    model, prompt_hash = selection['winner'], selection['prompt_hash']
    if prompt_hash != benchmark.PROMPT_HASH:
        raise RuntimeError('Prompt changed after model comparison; rerun benchmark')
    view_sql = f'''CREATE OR REPLACE VIEW {hn.BASE}.hn_job_posts AS
        WITH parsed AS (
          SELECT *, try_parse_json(normalized_json) result
          FROM {hn.BASE}.hn_extraction_validated
          WHERE model={pilot.literal(model)} AND prompt_hash='{prompt_hash}'
        )
        SELECT s.item_id, s.month, s.created_at_unix, s.source_url, s.text_plain,
          f.model, f.prompt_hash, f.processed_at, f.extraction_status, f.validation_issues,
          try_variant_get(f.result,'$.response.is_hiring_ad','BOOLEAN') is_hiring_ad,
          try_variant_get(f.result,'$.response.skills','ARRAY<STRING>') skills,
          try_variant_get(f.result,'$.response.salary',
            'ARRAY<STRUCT<raw_text:STRING,minimum:DOUBLE,maximum:DOUBLE,currency:STRING,period:STRING>>') salary,
          try_variant_get(f.result,'$.response.seniority','ARRAY<STRING>') seniority,
          f.result:response.remote_policy::STRING remote_policy,
          f.result:response.remote_restrictions::STRING remote_restrictions,
          try_variant_get(f.result,'$.response.country','ARRAY<STRING>') country,
          f.result:response.location_text::STRING location_text,
          f.result:error_message::STRING extraction_error
        FROM {hn.BASE}.hn_extraction_inputs s JOIN parsed f
          ON s.item_id=f.item_id AND s.input_hash=f.input_hash'''
    config = {'model': model, 'prompt_hash': prompt_hash,
              'model_sql': benchmark.model_sql(model, '__SOURCE__'), 'view_sql': view_sql}
    config_path = hn.DATA / 'extraction_config.json'
    config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    hn.cli('fs', 'cp', str(config_path), 'dbfs:' + hn.VOLUME + '/extraction_config.json', '--overwrite')
    remote = '/Shared/tech_careers'
    hn.cli('workspace', 'mkdirs', remote)
    hn.cli('workspace', 'import', remote + '/validate_hn_extraction.py', '--format', 'RAW', '--file',
           str(hn.ROOT / 'scripts/validate_hn_extraction.py'), '--overwrite')
    hn.cli('workspace', 'import', remote + '/extract_hn_archive', '--format', 'SOURCE', '--language', 'PYTHON',
           '--file', str(hn.ROOT / 'notebooks/extract_hn_archive.py'), '--overwrite')
    job = {'name': 'Tech Careers - HN archive extraction', 'performance_target': 'STANDARD',
           'tags': {'aidevkit_project': 'ai-dev-kit', 'project': 'tech-careers'},
           'max_concurrent_runs': 1,
           'tasks': [{'task_key': 'extract_archive', 'notebook_task': {'notebook_path': remote + '/extract_hn_archive', 'source': 'WORKSPACE'},
                      'timeout_seconds': 28800, 'max_retries': 0}]}
    job_path = hn.DATA / 'archive_job.json'
    job_path.write_text(json.dumps(job), encoding='utf-8')
    if previous:
        reset_path = hn.DATA / 'archive_job_reset.json'
        reset_path.write_text(json.dumps({'job_id': previous['job_id'], 'new_settings': job}), encoding='utf-8')
        hn.cli('jobs', 'reset', '--json', '@' + str(reset_path))
        created = {'job_id': previous['job_id']}
    else:
        created = json.loads(hn.cli('jobs', 'create', '--json', '@' + str(job_path), '--output', 'json'))
    started = json.loads(hn.cli('jobs', 'run-now', str(created['job_id']), '--no-wait', '--output', 'json'))
    record = {'job_id': created['job_id'], 'run_id': started['run_id'], 'model': model, 'prompt_hash': prompt_hash}
    run_record.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    run()
