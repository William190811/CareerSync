# Tech Career Explorer

Initial load verified on 26 October 2026: 82 monthly threads (January 2020 through
October 2026), 43,450 top-level records, 40,767 with text and 2,683 unavailable.
No missing months or duplicate post IDs were found. Databricks table counts,
available-text counts, and expected comment IDs reconcile for every thread.
October is an in-progress snapshot, not a completed month.

## Raw Hacker News archive

`scripts/ingest_hn.py` collects the monthly **Ask HN: Who is hiring?** threads
published by `whoishiring` from January 2020 onward. It uses the official HN API
for discovery and authoritative top-level comment IDs, Algolia for bulk comment
text, and the official API for missing or empty indexed comments.

This is an unclassified raw archive. Top-level comments can include discussion or
other non-advertisements. Deleted/unavailable text cannot be recovered. Replies
are excluded. Structured roles, skills, salary, seniority, and remote policy will
be extracted in the next stage.

### Run

Requires Python 3.10+, the Databricks CLI, and authenticated profile `tech-career`.
Uses only the Python standard library. The configured warehouse belongs to this
project's workspace.

```powershell
python scripts/ingest_hn.py download
python scripts/ingest_hn.py check
python scripts/ingest_hn.py load
```

Downloads are checkpointed by month under ignored `data/hn/`. Failures stop the
run rather than silently skipping records. Completed historical months are
reused if the official comment ID list is unchanged; the current month is fetched
again. Local downloads stage the initial transfer; no external hosting is used.

### Databricks destinations

- `workspace.tech_careers.hn_raw_posts`: one row per top-level comment ID, including
  HTML, plain text, source, timestamps, unavailable flags, and preserved JSON.
- `workspace.tech_careers.hn_raw_threads`: monthly coverage, authoritative IDs,
  expected/loaded/available counts, title, and preserved thread JSON.
- `/Volumes/workspace/tech_careers/ingestion/`: uploaded JSONL snapshots.

Loads merge by ID, allowing safe reruns without duplicate inserts. Existing
records outside a snapshot are retained. Free Edition SQL compute quotas still
apply. No model calls or AI extraction run during ingestion.

Coverage and download counts are saved in `data/hn/summary.json`. The loader reads
back table totals, checks duplicates, and reconciles per-thread record counts.

### Sources

- https://github.com/HackerNews/API
- https://hn.algolia.com/api

Archive text can contain contact information published in the original posts.
The raw archive is intended for this workspace, not for a public contact directory.

## AI extraction pilot

The first 20 chronological records are materialized in
`workspace.tech_careers.hn_extraction_sample20_inputs`. Databricks `ai_extract`
extracts skills, numeric salary offers, seniority, remote policy/restrictions,
and explicitly stated countries. Two unavailable records are retained as skipped;
18 readable posts have reviewed results.

The latest accepted output is exposed through
`workspace.tech_careers.hn_extraction_sample20`. Full model outputs, error messages,
source hashes, timestamps, and extraction versions are persisted in
`workspace.tech_careers.hn_extraction_sample20_results`. The history includes
earlier pilot attempts, so its row count exceeds 20.

```powershell
python scripts/extract_hn_sample.py
python scripts/extract_hn_sample.py --check-only
```

The normal command reuses existing accepted results. The check-only command makes
no AI calls. Targeted retries are restricted to the fixed sample and current
extraction version, using `--retry-items <id> ...`. The full archive is not processed.

Reviewed expectations are in `tests/fixtures/hn_first20_expected.json`; results
and limitations are in `reports/ai-extraction-pilot.md`. Missing countries and
salary periods are not guessed. Skills and seniority are post-level unions, not
role-specific requirements. Generalizing the pilot to all posts requires further
quality evaluation and user authorization.

## Model comparison and full archive

The user subsequently authorized a model comparison and full-archive processing.
`scripts/benchmark_hn_models.py` compares GPT OSS 120B and 20B, Qwen3 Next 80B,
Qwen3.5 122B, Llama 3.3 70B, and a fresh ai_extract precision baseline on the same development sample.
Raw model outputs are stored in `workspace.tech_careers.hn_model_benchmark`.
See `reports/model-comparison.md` for measured failures, timing, and limitations.
GPT OSS 120B was selected after source-spelling alignment; raw answers are preserved.

```powershell
python scripts/benchmark_hn_models.py
python -m unittest discover -s tests -p test_extraction_validation.py
python scripts/start_hn_archive.py
```

`start_hn_archive.py` deploys the notebook and validation helper to
`/Shared/tech_careers`, writes the exact model/prompt configuration to the existing
ingestion volume, and launches the saved **Tech Careers - HN archive extraction**
job in STANDARD serverless mode. There is no recurring schedule or paid fallback.
The script refuses to start another run while one is active, and reuses the job
after termination. Completed batches are reused on rerun.
The saved task allows up to eight hours per run, retaining STANDARD compute and
all Free Edition limits. An extended timeout is not a paid upgrade.

Full-archive destinations:

- `workspace.tech_careers.hn_extraction_inputs`: stable source snapshot.
- `workspace.tech_careers.hn_extraction_inferences`: persisted raw model responses.
- `workspace.tech_careers.hn_extraction_validated`: aligned outputs and validation flags.
- `workspace.tech_careers.hn_job_posts`: typed, app-facing review view.

The job checkpoints every 500 readable posts and retains unavailable records
without inference. Status values are `ready`, `needs_review`, `non_hiring`,
`failed`, and `skipped_unavailable`. Charts should use `ready` rows and disclose
the excluded/review counts. A successful job means all input IDs were processed,
not that every extraction is factually correct. Automated checks cannot establish
complete recall or resolve every ambiguous advertisement. Errors are preserved;
a batch with at least 50% inference failures stops the run for investigation.

Run IDs are saved locally in ignored `data/hn/full_extraction_run.json`.
Free Edition quotas may interrupt the job; a launched run is not proof of completion.
