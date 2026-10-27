# CareerSync

A student focused hiring market dashboard built from Hacker News **Who is hiring?** posts from 2020 onward. Explore observed skills, advertised salary, seniority, location, and work policy, then compare tech careers with general university subjects.

The interface is implemented in a dark-only theme, including archive coverage, filters, charts, a paginated source feed, major shortlists, shared demo profiles, and Genie chat. The production app runs on Databricks Free Edition. Anyone in the workspace `users` group can open it after signing in to Databricks: [Open CareerSync](https://tech-career-explorer-7474648668828954.aws.databricksapps.com). The latest verified snapshot has 43,450 processed input posts: 38,615 are ready for market charts; the rest are marked for review, non-hiring, failed, or unavailable.

## Quick start for students

1. [Open CareerSync](https://tech-career-explorer-7474648668828954.aws.databricksapps.com) and choose a career or browse the six tech career paths.
2. Filter hiring posts by country, seniority, work arrangement, or year.
3. Review the skills, salary ranges, and original Hacker News posts behind the charts.
4. Select up to three university subjects and compare how they connect to the career you chose.
5. Optionally save a shared demo profile or ask a market question in the configured Tech Career Market Explorer Genie space.

Counts describe job advertisements, not unique vacancies or the entire job market. AI-extracted fields may need review. Market charts use only rows marked `ready`; archive coverage and status counts include all processed source IDs. Salary currency and pay period are kept separate.

## Run locally

Requires Python 3.10+, Node.js, npm, Databricks CLI, and access to the approved Databricks Free Edition workspace. Do not add credentials to this repository.

1. Clone the private repository and install dependencies:

   ```powershell
   git clone https://github.com/William190811/tech-career-explorer.git
   cd tech-career-explorer
   python -m pip install -r requirements.txt
   cd frontend
   npm install
   cd ..
   ```

2. Sign in with the `tech-career` profile and find the workspace SQL warehouse:

   ```powershell
   databricks auth login --host https://dbc-a91ad0f7-7fcd.cloud.databricks.com --profile tech-career
   databricks warehouses list --profile tech-career
   ```

3. In a PowerShell window, set your local profile and warehouse ID, then start FastAPI:

   ```powershell
   $env:DATABRICKS_CONFIG_PROFILE = "tech-career"
   $env:DATABRICKS_WAREHOUSE_ID = "<warehouse-id>"
   $env:DATABRICKS_GENIE_SPACE_ID = "01f1d1ed1c27120da38f5f10cd586606"
   python -m uvicorn api.app:app --reload --port 8001
   ```

4. In another window, start Vite:

   ```powershell
   cd frontend
   npm run dev
   ```

   Open the local URL printed by Vite. The frontend proxies `/api` requests to FastAPI. The Databricks SQL warehouse and the Tech Career Market Explorer Genie space must be available to your workspace identity. Genie answers are grounded in the processed Hacker News posts and may change as extraction continues.

## Project map

- `frontend/`: React dashboard and visual system.
- `api/`: FastAPI endpoints for the dashboard, source posts, demo profiles, and Genie.
- `scripts/` and `notebooks/`: HN ingestion, extraction, validation, and app packaging.
- `reports/`: model evaluation, extraction progress, and data limitations.

## Codebase map

The Graphify overview is in [`graphify-out/GRAPH_REPORT.md`](graphify-out/GRAPH_REPORT.md), with an interactive view at [`graphify-out/graph.html`](graphify-out/graph.html). To refresh it after changing code or architecture docs, install Graphify locally and run `graphify . --update`. The post-commit hook is local to each clone, so install it with `graphify hook install`.

The market API reads `workspace.tech_careers.hn_job_posts` and uses `extraction_status = 'ready'` for analysis. Follow the progress reports for the latest verified extraction counts.

See [USER_GUIDE.md](USER_GUIDE.md) for feature behavior, profile purpose, filter scope, limitations, and the manual acceptance checklist. See the Databricks deployment section in [IMPLEMENTATION.md](IMPLEMENTATION.md) for workspace resources and permission prerequisites.

Databricks Free Edition allows up to three Apps per account. Apps stop automatically after 24 hours and can be restarted. See the [Free Edition limits](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).
