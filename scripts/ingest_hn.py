"""Download monthly HN hiring posts and merge raw records into Databricks."""
import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'hn'
CLI = shutil.which('databricks') or str(next((Path(os.environ['LOCALAPPDATA']) / 'Microsoft/WinGet/Packages').glob('Databricks.DatabricksCLI_*/databricks.exe')))
PROFILE = 'tech-career'
WAREHOUSE = '437867c6b7e08dcc'
BASE = 'workspace.tech_careers'
VOLUME = '/Volumes/workspace/tech_careers/ingestion'


def get(url):
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'StudentCareerResearch/1.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def official(item_id):
    return get(f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json')


def cli(*args):
    result = subprocess.run([CLI, *args, '-p', PROFILE], capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout


def sql(statement):
    request = DATA / f'sql_request_{os.getpid()}.json'
    request.write_text(json.dumps({'warehouse_id': WAREHOUSE, 'statement': statement, 'wait_timeout': '50s', 'on_wait_timeout': 'CONTINUE'}), encoding='utf-8')
    result = json.loads(cli('api', 'post', '/api/2.0/sql/statements', '--json', '@' + str(request)))
    while result['status']['state'] in ('PENDING', 'RUNNING'):
        time.sleep(3)
        result = json.loads(cli('api', 'get', '/api/2.0/sql/statements/' + result['statement_id']))
    if result['status']['state'] != 'SUCCEEDED':
        raise RuntimeError(json.dumps(result['status']))
    return result.get('result', {}).get('data_array', [])


def month_key(timestamp):
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).strftime('%Y-%m')


def download_thread(thread):
    month = month_key(thread['time'])
    target = DATA / 'months' / f'{month}-{thread["id"]}.json'
    if target.exists():
        cached = json.loads(target.read_text(encoding='utf-8'))
        if cached['coverage']['expected_ids'] == sorted(thread.get('kids', [])) and month != dt.datetime.now(dt.timezone.utc).strftime('%Y-%m'):
            return cached
    indexed = get(f'https://hn.algolia.com/api/v1/items/{thread["id"]}')
    children = {int(c['id']): c for c in indexed.get('children', [])}
    rows = []
    fetched = dt.datetime.now(dt.timezone.utc).isoformat()
    for item_id in thread.get('kids', []):
        item = children.get(item_id)
        source = 'algolia'
        if item is None or not item.get('text'):
            item = official(item_id)
            source = 'hn_firebase'
        item = item or {'id': item_id, 'unavailable': True}
        parent = item.get('parent', item.get('parent_id'))
        if parent is not None and int(parent) != thread['id']:
            raise ValueError(f'Wrong parent for {item_id}')
        text = item.get('text') or ''
        rows.append({'item_id': item_id, 'thread_id': thread['id'], 'month': month,
                     'author': item.get('by', item.get('author')), 'created_at_unix': item.get('time', item.get('created_at_i')),
                     'text_html': text, 'text_plain': html.unescape(re.sub('<[^>]+>', ' ', text)),
                     'deleted': bool(item.get('deleted')), 'dead': bool(item.get('dead')),
                     'unavailable': not bool(text), 'source': source,
                     'source_url': f'https://news.ycombinator.com/item?id={item_id}',
                     'fetched_at': fetched, 'raw_json': json.dumps(item, ensure_ascii=False)})
    coverage = {'thread_id': thread['id'], 'month': month, 'title': thread['title'],
                'source_url': f'https://news.ycombinator.com/item?id={thread["id"]}',
                'expected_ids': sorted(thread.get('kids', [])), 'expected_count': len(thread.get('kids', [])),
                'loaded_count': len(rows), 'available_count': sum(not r['unavailable'] for r in rows),
                'fetched_at': fetched, 'raw_json': json.dumps(thread)}
    result = {'coverage': coverage, 'rows': rows}
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    temporary.replace(target)
    return result


def download():
    (DATA / 'months').mkdir(parents=True, exist_ok=True)
    ids = get('https://hacker-news.firebaseio.com/v0/user/whoishiring.json')['submitted']
    cutoff = int(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        items = list(pool.map(official, ids))
    threads = sorted([i for i in items if i and i.get('time', 0) >= cutoff and
                      re.fullmatch(r'Ask HN: Who is hiring\? \([^)]+\)', i.get('title', ''), re.I)], key=lambda i: i['time'])
    if not threads:
        raise RuntimeError('No hiring threads discovered')
    print(f'Discovered {len(threads)} monthly hiring threads', flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(download_thread, threads):
            results.append(result)
            c = result['coverage']
            print(f'{c["month"]}: {c["loaded_count"]} records, {c["available_count"]} with text', flush=True)
    for name, rows in [('posts', [r for result in results for r in result['rows']]),
                       ('threads', [result['coverage'] for result in results])]:
        directory = DATA / name
        directory.mkdir(exist_ok=True)
        (directory / 'snapshot.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    months = {r['coverage']['month'] for r in results}
    current = dt.datetime.now(dt.timezone.utc)
    expected = {f'{y:04}-{m:02}' for y in range(2020, current.year + 1) for m in range(1, 13) if (y, m) <= (current.year, current.month)}
    summary = {'thread_count': len(results), 'raw_post_count': sum(len(r['rows']) for r in results),
               'available_post_count': sum(r['coverage']['available_count'] for r in results),
               'missing_months': sorted(expected - months), 'first_month': min(months), 'last_month': max(months)}
    (DATA / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary), flush=True)


def load():
    if not (DATA / 'summary.json').exists():
        raise RuntimeError('Complete the download before loading')
    sql(f'CREATE SCHEMA IF NOT EXISTS {BASE}')
    sql(f'CREATE VOLUME IF NOT EXISTS {BASE}.ingestion')
    schemas = {
        'posts': 'item_id BIGINT, thread_id BIGINT, month STRING, author STRING, created_at_unix BIGINT, text_html STRING, text_plain STRING, deleted BOOLEAN, dead BOOLEAN, unavailable BOOLEAN, source STRING, source_url STRING, fetched_at STRING, raw_json STRING',
        'threads': 'thread_id BIGINT, month STRING, title STRING, source_url STRING, expected_ids ARRAY<BIGINT>, expected_count BIGINT, loaded_count BIGINT, available_count BIGINT, fetched_at STRING, raw_json STRING'}
    for name, schema in schemas.items():
        remote = f'{VOLUME}/{name}/snapshot.jsonl'
        cli('fs', 'mkdir', 'dbfs:' + f'{VOLUME}/{name}')
        cli('fs', 'cp', str(DATA / name / 'snapshot.jsonl'), 'dbfs:' + remote, '--overwrite')
        table = f'{BASE}.hn_raw_{name}'
        sql(f'CREATE TABLE IF NOT EXISTS {table} ({schema}) USING DELTA')
        key = 'item_id' if name == 'posts' else 'thread_id'
        sql(f"MERGE INTO {table} t USING (SELECT * FROM read_files('{remote}', format => 'json', schema => '{schema}')) s ON t.{key} = s.{key} WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *")
        print(f'{table}: {sql(f"SELECT COUNT(*) FROM {table}")}', flush=True)
    print('Coverage check:', sql(f'SELECT MIN(month), MAX(month), COUNT(*), SUM(expected_count), SUM(loaded_count), SUM(available_count) FROM {BASE}.hn_raw_threads'), flush=True)
    duplicates = sql(f'SELECT COUNT(*) - COUNT(DISTINCT item_id) FROM {BASE}.hn_raw_posts')
    print('Duplicate check:', duplicates, flush=True)
    if int(duplicates[0][0]) != 0:
        raise RuntimeError('Duplicate post IDs in destination')
    mismatches = sql(f'''SELECT t.thread_id FROM {BASE}.hn_raw_threads t
        LEFT JOIN (SELECT thread_id, COUNT(*) n, COUNT_IF(NOT unavailable) available, COLLECT_SET(item_id) ids FROM {BASE}.hn_raw_posts GROUP BY thread_id) p
        ON t.thread_id = p.thread_id
        WHERE COALESCE(p.n, 0) <> t.expected_count OR COALESCE(p.available, 0) <> t.available_count
           OR SIZE(ARRAY_EXCEPT(t.expected_ids, p.ids)) > 0''')
    if mismatches:
        raise RuntimeError(f'Thread counts do not reconcile: {mismatches}')
    print('Every thread reconciles with its stored posts', flush=True)


def self_check():
    assert month_key(1577836800) == '2020-01'
    assert month_key(1609459200) == '2021-01'
    assert re.fullmatch(r'Ask HN: Who is hiring\? \([^)]+\)', 'Ask HN: Who is hiring? (January 2020)', re.I)
    assert not re.fullmatch(r'Ask HN: Who is hiring\? \([^)]+\)', 'Ask HN: Who wants to be hired? (January 2020)', re.I)
    for path in (DATA / 'months').glob('*.json'):
        result = json.loads(path.read_text(encoding='utf-8'))
        ids = [r['item_id'] for r in result['rows']]
        assert sorted(ids) == result['coverage']['expected_ids']
        assert len(ids) == len(set(ids))
    print('Self-check passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['download', 'load', 'check'])
    action = parser.parse_args().action
    {'download': download, 'load': load, 'check': self_check}[action]()
