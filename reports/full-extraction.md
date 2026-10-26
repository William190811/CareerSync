# Full archive extraction

Status verified on 26 October 2026 at 10:28 Jakarta time: **RUNNING, not complete.**

The user-authorized follow-up resumed the previously paused job. The expanded
benchmark still selects system.ai.gpt-oss-120b; the deployed model and prompt
hash match that selection. No model switch or paid service was introduced.

100 successful staged speed-test outputs were merged into the raw inference
archive while no job was active. They will be validated on startup rather than
sent for inference again. Readback found **5,301 raw rows and 5,301 unique IDs**,
out of 43,450 source records. This includes 2,683 unavailable records.

Last validated view counts before resume:

| Category | Records |
|---|---:|
| Ready after automated checks | 2,413 |
| Needs review | 47 |
| Non-hiring | 58 |
| Unavailable source text | 2,683 |
| Failed inference | 0 |
| Total validated at that readback | 5,201 |

The additional 100 staged rows were not yet included in those validated counts.
These are interim counts, not completion evidence.

[Open resumed Databricks run](https://dbc-a91ad0f7-7fcd.cloud.databricks.com/?o=7474648668828954#job/725689464016621/run/796013271359123)

The job retains STANDARD serverless compute and checkpoints every 500 readable
posts, repartitioned into 32 partitions before inference. Its task timeout was
increased from four to eight hours because the measured batch pace could exceed
four hours; this does not upgrade the workspace or remove Free Edition quotas.
The saved job is reused rather than creating duplicate jobs or concurrent runs.

The completion follow-up stays quiet while processing is active or unchanged.
App development can proceed using the partial data, with coverage labeled.

Use workspace.tech_careers.hn_job_posts for typed review outputs. Charts must
filter to xtraction_status = 'ready' and disclose excluded/review counts.
Automated checks do not establish that every extracted fact is accurate or that
all skills were recalled. Final source/output reconciliation has not run yet.
