# Model comparison

All candidates used the same 18 readable posts, schema, instructions, and reviewed expectations; two unavailable records were retained as skipped.

| Candidate | Readable successes | Check failures | SQL inference seconds |
|---|---:|---:|---:|
| system.ai.gpt-oss-120b | 18/18 | 0 | 28.98 |
| ai_extract_precision | 18/18 | 2 | 48.77 |
| system.ai.meta-llama-3-3-70b-instruct | 18/18 | 18 | 12.27 |
| system.ai.qwen3-next-80b-a3b-instruct | 18/18 | 23 | 18.28 |
| system.ai.gpt-oss-20b | 16/18 | 3 | 69.0 |
| system.ai.qwen35-122b-a10b | 0/18 | 18 | 110.17 |

Selected: **system.ai.gpt-oss-120b**. Selection prioritizes successful responses, then fewer check failures, then lower elapsed time.

Evidence alignment restores exact source spelling only when characters match apart from whitespace or case, and keeps raw outputs unchanged. Scores above include that same alignment for every candidate.

Timing includes SQL overhead and is not per-request latency or a cost estimate. This is a small, previously tuned January 2020 development sample, not an independent accuracy benchmark. No universal model-quality claim follows from it. ai_extract uses a Databricks-managed model whose identity is not exposed by this test.

## system.ai.gpt-oss-120b

No reviewed-check failures.

## ai_extract_precision

- 21936486: seniority: expected ['manager'], got []
- 21936562: remote_policy: expected onsite, got not_stated

## system.ai.meta-llama-3-3-70b-instruct

- 21936441: remote_policy: expected remote, got mixed
- 21936441: seniority: expected ['experienced_unspecified'], got ['experienced']
- 21936475: location_text is not a source quote
- 21936486: country: expected [], got ['United Kingdom']
- 21936486: location_text is not a source quote
- 21936492: location_text is not a source quote
- 21936536: remote_policy: expected remote, got mixed
- 21936542: location_text is not a source quote
- 21936550: country: expected [], got ['Germany']
- 21936550: seniority: expected ['head', 'intern', 'student'], got ['intern', 'student', 'Head']
- 21936550: seniority_evidence is not a source quote
- 21936562: remote_policy: expected onsite, got mixed
- 21936576: country: expected [], got ['United States']
- 21936576: seniority: expected ['manager', 'chief'], got ['not_stated']
- 21936580: seniority: expected [], got ['experienced_unspecified']
- 21936589: remote_policy: expected remote, got mixed
- 21936643: country: expected [], got ['United States']
- 21936686: seniority: expected ['intern', 'manager'], got ['intern']

## system.ai.qwen3-next-80b-a3b-instruct

- 21936441: country: expected [], got ['United States', 'Canada']
- 21936475: country: expected ['Germany'], got ['Germany', 'United Kingdom']
- 21936475: location_text is not a source quote
- 21936486: country: expected [], got ['United Kingdom', 'United States']
- 21936486: seniority: expected ['manager'], got ['manager', 'engineer']
- 21936486: location_text is not a source quote
- 21936492: location_text is not a source quote
- 21936542: country: expected [], got ['United States', 'Canada']
- 21936550: country: expected [], got ['Germany']
- 21936550: seniority_evidence is not a source quote
- 21936558: country: expected [], got ['United States']
- 21936576: country: expected [], got ['United States']
- 21936576: seniority: expected ['manager', 'chief'], got ['chief']
- 21936576: missing explicitly stated skill Linux
- 21936580: seniority: expected [], got ['mid']
- 21936580: country_evidence is not a source quote
- 21936593: country: expected [], got ['United States']
- 21936643: country: expected [], got ['United States']
- 21936650: country: expected ['Ireland'], got ['Ireland', 'United States']
- 21936650: salary period: expected not_stated, got year
- 21936684: country: expected [], got ['United States']
- 21936686: country: expected [], got ['United States']
- 21936686: seniority: expected ['intern', 'manager'], got ['intern']

## system.ai.gpt-oss-20b

- 21936441: {}
- 21936486: {}
- 21936684: seniority: expected ['manager'], got []

## system.ai.qwen35-122b-a10b

- 21936441: {}
- 21936475: {}
- 21936486: {}
- 21936492: {}
- 21936536: {}
- 21936542: {}
- 21936550: {}
- 21936558: {}
- 21936562: {}
- 21936576: {}
- 21936580: {}
- 21936589: {}
- 21936593: {}
- 21936643: {}
- 21936650: {}
- 21936653: {}
- 21936684: {}
- 21936686: {}
