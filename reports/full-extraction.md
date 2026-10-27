# Full archive extraction

## Latest verified run, 27 October 2026

The Databricks job completed successfully. The dashboard's live warehouse response reported 43,450 distinct source IDs and 43,450 distinct processed IDs. Counts below are from the `workspace.tech_careers` dashboard tables and describe records by `extraction_status`:

| Status | Distinct posts |
|---|---:|
| Ready for market analysis | 38,615 |
| Needs review | 989 |
| Non-hiring | 1,157 |
| Failed | 6 |
| Skipped unavailable | 2,683 |
| **Total processed** | **43,450** |

- Model: `system.ai.gpt-oss-120b`
- Job: [725689464016621](https://dbc-a91ad0f7-7fcd.cloud.databricks.com/?o=7474648668828954#job/725689464016621)
- Successful run: [210461830608894](https://dbc-a91ad0f7-7fcd.cloud.databricks.com/?o=7474648668828954#job/725689464016621/run/210461830608894)
- Task run: `354637176805019`
- Prompt hash: `810320a19c67acdcc4cd99ddd9f004963272af767a8f2c079680ce973546ff8b`
- Run completed: 27 October 2026, 10:31 UTC

The live duplicate audit verified 43,450 total rows, 43,450 distinct `item_id` values, zero duplicate IDs, and zero null IDs. Status counts matched the 43,450 input records. The six failed records were also inspected: four have an explicit free daily foundation-model quota error from 27 October 2026; two have `inference_error_or_invalid_json` with no specific error text. Do not retry quota-blocked rows until at least 24 hours after that failure. The two unexplained inference failures remain unresolved. The 989 `needs_review` records remain flagged and should not be treated as manually validated. AI-extracted fields can be incomplete or wrong.

The app's market charts use only the 38,615 `ready` records. They exclude review-needed, non-hiring, failed, and unavailable records. Coverage is based on distinct post IDs. Hacker News posts are a sample of hiring activity, not a census of tech employment.

All extraction and dashboard work stayed within Databricks Free Edition. No paid service was enabled. Do not upgrade compute to address quota or resource limits.
