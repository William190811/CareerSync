# Tech Career Explorer

Explore tech hiring trends and compare university majors for the career you want.
The project combines Hacker News **Who is hiring?** posts from 2020 onward with
source-backed educational guidance for students.

**Status:** The data pipeline is implemented and full-archive AI extraction is
underway. The web interface and educational guidance are planned. There is no
deployed app link yet.

## Planned features

- **Market dashboard:** Hiring and skill trends, filtered by date, career,
  country, seniority, and remote policy.
- **Major comparisons:** Compare up to three subjects by curriculum, career
  relevance, prerequisites, and skill gaps, with official sources.
- **AI questions:** Explore market data through Databricks Genie and ask about
  educational pathways, with supporting evidence.
- **Demo profiles:** Save interests, favourite subjects, a target career, and
  shortlisted majors.
- **Transparent data:** Inspect original advertisements, unknown fields, and
  processing coverage. Use either a light or dark theme.

Initial careers: software engineering, AI/ML, data science, data engineering,
cybersecurity, and cloud/DevOps.

## Quick start for students

Once the app is deployed:

1. Open the app link and select or create a **demo profile**.
2. Browse the **market overview** and filter for a career that interests you.
3. Explore its **major pathways** and compare up to three subjects.
4. Save your shortlist and ask a question, such as "Which skills appear most
   often in data engineering posts?"
5. Review the sources and dataset coverage before drawing conclusions.

The app URL and sign-in instructions will be added after deployment. These
steps describe the intended experience, not currently available screens.

## Developer quick start

Requires Python 3.10+, Databricks CLI, and a Databricks Free Edition workspace.
This private repository requires collaborator access.

```powershell
git clone https://github.com/William190811/tech-career-explorer.git
cd tech-career-explorer
databricks auth login --host <your-workspace-url> --profile tech-career
python -m unittest discover -s tests -p test_extraction_validation.py
```

The scripts currently use the project's warehouse and `tech-career` profile.
Update the configuration in `scripts/ingest_hn.py` for another workspace.
Never commit credentials. Frontend startup instructions will follow when the
application is implemented.

## Technology and documentation

Planned app: **React, TypeScript, Tailwind CSS, shadcn/ui, Recharts, and FastAPI**,
hosted on Databricks Apps. The data pipeline uses Python, Databricks AI functions,
SQL, and Delta tables within Free Edition limits.

| Folder | Contents |
|---|---|
| `scripts/` | Ingestion, extraction, evaluation, and job deployment |
| `notebooks/` | Resumable Databricks processing |
| `tests/` | Validation tests and reviewed sample expectations |
| `reports/` | Evaluation results, processing status, and limitations |

App-facing view: `workspace.tech_careers.hn_job_posts`. Analytical queries should
use `extraction_status = 'ready'` and disclose excluded records.

## Data limitations

HN posts represent a sample of hiring activity, not the entire global job market.
Missing details remain unknown, and AI extraction can make mistakes. Salary
currencies and payment periods must be compared separately. A post may advertise
multiple roles; its combined skills do not apply to every role. Major pathways
are guidance, not guarantees of employment.

Sources: [official HN API](https://github.com/HackerNews/API) and
[HN Search by Algolia](https://hn.algolia.com/api).
