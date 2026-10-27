# CareerSync user and test guide

This guide explains how to use the student dashboard, what its figures mean, and how to check the features. CareerSync is deployed on Databricks Free Edition. Members of the workspace `users` group can open it after signing in to Databricks: [Open CareerSync](https://tech-career-explorer-7474648668828954.aws.databricksapps.com). It is not accessible anonymously.

## What the dashboard is for

Explore technology hiring signals from Hacker News **Who is hiring?** advertisements from 2020 onward. The app summarizes skills, advertised salary, seniority, country, and work arrangement, then connects six tech career paths to general university subjects.

The source is a sample of online advertisements, not a census of jobs or unique vacancies. Extracted facts can be incomplete or wrong. All 43,450 archived source IDs have been processed; charts use only records marked ready and exclude review-needed, failed, unavailable, and non-hiring records.

## Quick start

1. Open the [deployed CareerSync app](https://tech-career-explorer-7474648668828954.aws.databricksapps.com), or start the FastAPI backend and Vite frontend using the local setup in [README.md](README.md).
2. Choose **All tech roles** or select one of the career paths.
3. Narrow the results by country, seniority, work style, or starting year (including 2020).
4. Read the hiring trend, work arrangement, skills, salary groups, and source advertisements. Open a source post to check its original context.
5. Select up to three subjects to compare their curriculum topics and preparation notes.
6. Optionally save the current career and subject shortlist as a named class demo profile, or ask Genie a market question.

Choose **All locations**, **All levels**, **Any policy**, and **All years** to clear the filters. Use **Refresh** to reload market figures, archive status, source posts, and saved profiles.

## Market filters and figures

Every market query starts with posts marked `ready` and `is_hiring_ad = true`.

| Control or panel | What it changes | What may stay the same |
|---|---|---|
| Career | Headline count, trend, work arrangement, skill and salary summaries, and source feed. Career matching uses case-insensitive role phrases in the ad text, so it is an approximation. | Archive progress and processing-status counts are archive-wide. |
| Country | Market summaries and source feed using the extracted country field. | Archive progress and processing-status counts are archive-wide. Country names can have spelling or naming variants. |
| Seniority | Market summaries and source feed when the extracted seniority array contains the selected value. | Archive progress and processing-status counts are archive-wide. |
| Work style | Market summaries and source feed for remote, hybrid, onsite, mixed, or not stated policy. | Archive progress and processing-status counts are archive-wide. |
| From year | Includes that month and later through the latest configured archive month. The current app's end month is set to October 2026. | Archive progress and processing-status counts are archive-wide. |
| Archive coverage | Nothing. It describes the entire source archive and its processing status. | It should not move when a market filter changes. |
| University subjects | Changes the shortlist and comparison cards. | Curriculum descriptions are curated guidance, not live job-post metrics. |
| Demo profile | Loads a saved career and subject shortlist. Saving requires a profile name, except when updating an already saved profile. | It does not sign a student in, change the data, or narrow the market beyond the loaded career filter. |
| Genie chat | Sends the written question and conversation ID to the configured Genie space. | Dashboard filters and selected subjects are not automatically included in the question. |

The archive-coverage panel is intentionally global so students can see overall extraction progress. The **All posts** indicator and the “All posts” review/unavailable note distinguish these figures from filtered market metrics. Latest-month figures can change while extraction continues. A filter can return the same number when the chosen subset happens to have the same count, or when the source data contains no records for that combination. The source feed resets to its first page when a filter changes.

Career families are keyword approximations, and categories can overlap. A job ad may advertise multiple roles, so skills and seniority are ad-level signals rather than per-vacancy requirements. Salary groups keep currency and pay period separate, and salary summaries use only ads with a parsed minimum amount.

## Career and subject exploration

The six career paths are software engineer, AI/ML engineer, data scientist, data engineer, cybersecurity analyst, and cloud/DevOps engineer. Selecting a career filters the hiring data and suggests related subjects. Subject cards show a curriculum-topic summary, preparation notes, and links to professional curriculum guidance. They do not rank majors, establish university admission requirements, or promise employment.

Select up to three subjects. Selecting the same subject again removes it. The suggested subject cards and lower comparison list refer to the same shortlist.

## What the profile control does

The profile selector is an optional shortcut. Three starter profiles are built into the frontend. Choosing one sets a sample career and subject shortlist; it does not sign a student in or change the dataset independently of the market filters.

Saving a named demo profile stores its career and shortlist in the shared `workspace.tech_careers.student_demo_profiles` Delta table. Everyone with access to the app can see and use saved profiles. They are class examples, not private accounts. Use fictional names only and do not save sensitive student information. Only saved class profiles can be deleted; starter profiles are fixed examples.

The market dashboard works without profiles. If shared classroom presets are not useful, the profile selector, save panel, profile API routes, and profile table can be removed without removing filters, charts, subject comparisons, or Genie chat.

## Genie chat

Ask questions about the processed hiring archive, for example:

- “Which skills appear most in AI roles?”
- “How common are remote jobs?”
- “Compare data science and software engineering.”

Genie receives the question and conversation ID. It does not currently receive the dashboard's active filters, so its answer is not automatically narrowed to the selected career, country, seniority, work style, or year. Answers can be wrong; check the generated SQL and original ads. A live test returned the answer, generated SQL, and supporting result rows through the attachment-specific Databricks Genie endpoint.

## Feature and test checklist

### Automated checks

Run from the repository root. These checks use a fake SQL layer and mocked Genie replies, so they do not consume Databricks SQL or Genie usage:

```powershell
python -m unittest discover -s tests -v
cd frontend
npm.cmd run build
```

The dashboard API tests use a fake SQL-query function and mocked Genie SDK responses. They check:

- Filter parameter binding, all six career-family keyword expansions, and placeholder/parameter counts.
- Market response shape and filtering for metrics, with archive coverage/status queries kept global.
- Per-filter cache keys, the 60-second cache path, and manual-refresh bypass.
- Source-feed JSON decoding, SQL value binding, and pagination bounds.
- Shared profile listing, validation, upsert parameters, and delete validation.
- Genie conversation start/continue, answer/SQL/result parsing, and missing-space validation.
- Health and identity response shapes, profile write/delete failures, quota error messaging, and clear database-service errors.

The frontend has a production TypeScript build check but no automated browser interaction suite yet. These checks do not call Databricks and do not prove that workspace permissions, actual table contents, or remote query results are correct.

### Manual acceptance checklist

When the extraction job is idle, use the running app and check the following:

1. Select each career, country, seniority, work style, and year individually, including 2020. Confirm the request includes the selected value and that headline count, trend, work arrangement, salary and skill summaries, and source feed reflect matching records. Counts may legitimately stay equal if the matching subset has the same size. Confirm the source feed resets to page one after changing a filter.
2. Combine at least two filters, then choose the default options again. Confirm the market metrics return to the broader result set.
3. Confirm archive coverage, processed/queued/review/non-hiring/unavailable/failed totals stay global while market metrics change.
4. Move through source-feed pages and open an original Hacker News ad.
5. Select, remove, and attempt to select a fourth subject. Confirm the three-subject limit and career-based suggestions.
6. Choose each starter profile and confirm its career/shortlist. Confirm starter profiles are not saved or overwritten unless a separate name is entered. Save, reload, select, edit, and delete a disposable named profile only in a workspace where a shared test write is acceptable.
7. Confirm the dashboard uses its dark theme throughout; there is no theme toggle or saved theme preference.
8. Ask Genie a question and a follow-up. Check the answer, generated SQL, any supporting rows, and error display. Confirm the selected dashboard filters are not implicitly reflected in the question.
9. Test an empty result, a disconnected API, and a reached Free Edition limit. Confirm the app shows an explanatory state rather than stale charts that look like the new filter succeeded.
10. Review at desktop and mobile widths, keyboard navigation, and reduced-motion settings.

## Current verification record

- **Passed:** `python -m unittest discover -s tests -v` ran 26 backend/extraction-validation tests. The suite covers market filters, source posts, profiles, Genie, health/identity, and extraction validation. Dashboard API tests use mocked SQL and Genie SDK responses.
- **Passed:** `npm.cmd run build` completed TypeScript checking and the production build. Vite reported the main JavaScript bundle is 652.45 kB, above its 500 kB advisory threshold.
- **Passed:** `npm.cmd run lint` exited successfully with no warnings.
- **Passed:** `python -m py_compile api/app.py api/run.py tests/test_dashboard_api.py` completed successfully.
- **Passed:** browser smoke runs with mocked APIs checked that selected filters reach the backend, a career filter changes the headline count, 2020 is selectable, page two with exactly five posts has no extra page, a changed filter from page two sends one request for page one, starter profiles require a named copy, saved profiles can be selected and deleted, three subjects can be selected but not a fourth until one is removed, the dark dashboard renders, Genie answers render, archive coverage remains **All posts**, charts render from API responses, empty feeds are explained, failed market requests clear stale values, and refresh recovers. This was simulated data, not a live Databricks check.
- **Passed:** Graphify refreshed its code graph. SQL graph extraction was skipped because the optional `tree_sitter_sql` package is not installed.
- **Passed:** `python scripts/package_app.py` rebuilt the production bundle and refreshed the Databricks Apps source package. A local test-client check returned HTTP 200 for the staged app's home page and health route.
- **Passed:** After fixing parsing of newline characters inside encoded source text, the live Data scientist filter returned 1,608 matching posts and showed matching chart, skills, salary, and source-feed data. The Software engineering demo profile changed the filtered headline to 14,492 posts. A multiline source ad that previously broke the feed now renders, and the parser regression test passes.
- **Found and fixed:** The country dropdown was limited to the first 100 options. A read-only Genie One query confirmed 141 distinct country values in ready hiring posts. The dropdown now loads all 141; selecting United States changed the live headline from 38,615 to 10,701 posts.
- **Passed:** Strict Databricks bundle validation succeeded for both `dev` and `prod`; a dry-run sync listed only the staged app source and built frontend assets. The production app deployed successfully and CLI readback confirmed `RUNNING`, deployment `SUCCEEDED`, and active compute. The SQL warehouse, Genie space, and required tables are bound to the app.
- **Not supported by the current validator:** Databricks CLI v1.22.1 `apps validate --path .databricks_app` stops with “no supported project type detected (looking for package.json)” for this Python/FastAPI app. The staged package was checked locally instead; this CLI command did not verify deployment.
- **Passed:** The live local browser rendered workspace metrics and charts. Selecting Software engineer changed the headline from 38,615 to 14,492 posts, latest-month count from 250 to 91, and React mentions from 9,552 to 3,949. Archive coverage remained global at 43,450 processed of 43,450 inputs. The updated filtered response took about 10 seconds in this check; runtime varies.
- **Passed:** A live Genie question displayed the answer, generated SQL, and supporting result rows in the local frontend. The earlier missing rows were caused by use of a deprecated message-level endpoint; the app now fetches the result by attachment ID. The deployed app startup was verified, but a signed-in production Genie interaction remains unverified.
- **Passed:** A named demo profile was saved, selected, and deleted through the live UI. The test profile was removed and confirmed absent afterward.
- **Found and routed around:** A pre-existing API process on local port 8000 serves an older build. The development proxy and current local API default use port 8001, leaving the old process untouched.
- **Passed:** A live table audit verified 43,450 rows, 43,450 distinct IDs, zero duplicate IDs, and zero null IDs. The six failed extractions were inspected: four explicitly report a Free Edition daily inference limit; two have only a generic inference/invalid-JSON issue with no specific error. The quota-blocked rows were not retried within the 24-hour limit.

## Known limitations

- All 43,450 source rows have been processed. The dashboard currently has 38,615 `ready`, 989 `needs_review`, 1,157 `non_hiring`, 6 `failed`, and 2,683 `skipped_unavailable` rows. The processed count describes source coverage, not the number of usable job advertisements.
- Four quota-blocked inference rows await a safe retry after the 24-hour window, and two invalid-JSON failures have no more specific diagnostic. The `needs_review` rows have not been manually reviewed.
- Career matching is based on role phrases in advertisement text, not a verified role taxonomy.
- Dashboard filters do not flow into Genie questions.
- Genie answers are not automatically narrowed to the dashboard filters; include the desired role, location, seniority, work style, or time period in the question.
- The health endpoint reports application liveness and whether a warehouse is configured. It does not run a SQL query; a successful market request is the stronger check of live data connectivity.
- Local Genie and profile flows were live-tested with the connected workspace identity. The deployed app's workspace `users` group has `CAN_USE`, and the required resources are attached. A signed-in teammate browser test remains outstanding.
- Demo profiles are shared within the workspace and are not private student records.
- The app requires Databricks sign-in and is available to workspace users. It is not public to anonymous visitors.
