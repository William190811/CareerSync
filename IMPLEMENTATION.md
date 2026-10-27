# CareerSync implementation

**Status:** CareerSync is deployed on Databricks Free Edition and is running at [the production app URL](https://tech-career-explorer-7474648668828954.aws.databricksapps.com). Workspace members in the `users` group have `CAN_USE`; the app owner and admins retain management access. The production deployment completed successfully. The archive extraction job is separate.

## 1. Outcome and architecture

Build and deploy the working student application using the supplied 21st.dev dashboard as a close visual reference. Create the private repository **`William190811/tech-career-explorer`** for collaboration.

Keep the agreed stack:

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | CSS design tokens and small house components |
| Charts and motion | Recharts and reduced-motion-aware CSS transitions |
| Backend | Python, FastAPI, Pydantic |
| Analytics and demo profiles | Databricks SQL and Delta tables |
| Market questions | Dedicated Databricks Genie space |
| Educational explanations | Curated official sources and a Databricks-hosted model |
| Hosting | One Databricks App serving the frontend and API |

The frontend uses npm, as recorded by its `package-lock.json`. FastAPI serves the production frontend build through the same origin and binds to `DATABRICKS_APP_PORT`.

Development can proceed while extraction continues. The app must show actual processing coverage throughout.

## 2. Interface and student experience

### Visual direction: follow the supplied dashboard closely

The approved reference is the attached 21st.dev `web3-bento.tsx` component and
its dark dashboard screenshot. Treat its composition, panel proportions,
layering, colors, typography, and interactions as the visual specification.
The supplied crypto copy and demo data are examples to replace, not product
requirements. The replacement has been reviewed in its dark theme at 1440px
and reflowed at 390px.

Preserve the reference's first-screen arrangement: a wide lead panel across two
columns, a stacked-card panel beside it, and a compact status panel at the far
right. Below, use a large chart spanning two columns, supporting panels in the
center, and one saturated lime panel spanning the right column vertically. Keep
the compact four-column desktop grid, rounded panels near 26px, tight consistent
gaps, thin quiet borders, dark near-black canvas, charcoal panels, vivid lime
primary accent, lilac secondary accent, bright text, muted gray support text,
and monospaced tabular figures. Derive color tokens from the supplied screenshot
and component defaults, including its lime `oklch(0.89 0.2 128)` and lilac
`oklch(0.74 0.12 300)` accents. Do not introduce a fixed left sidebar, a generic
marketing hero, a uniform grid of small white cards, or a different visual
system. The screen should read as the supplied dashboard at a glance. The
rejected starter dashboard has been replaced by the reference-aligned bento
implementation in `frontend/src/App.tsx` and `frontend/src/style.css`.

Use the supplied component as the starting point at
`frontend/src/components/ui/web3-bento.tsx`; preserve and adapt its tile
structure, four-column placement, stacked-card interaction, chart treatment,
and typography. Keep the React/TypeScript and small house-component structure.
Adapt the shell to a student market dashboard rather than rebuilding the same
arrangement from unrelated generic cards. Use the dark reference palette as the
sole appearance.

| Reference tile or interaction | Career Explorer equivalent |
|---|---|
| Greeting, headline metric, and short activity bars | Profile greeting, verified posting count, and actual monthly hiring activity |
| Overlapping payment-card stack | Up to three saved majors; selecting a card brings that major forward and updates the comparison |
| Gas gauge and speed selector | Actual archive coverage and extraction status; no invented live gauge values |
| Large performance-vs-benchmark chart | Actual monthly hiring-post trend; any comparison series must use a clearly stated, complete-enough source period |
| Allocation breakdown | Observed remote, hybrid, onsite, mixed, and unstated policy counts |
| Bright staking panel | Selected tech career, related posting signal, and its observed skills, with no invented rewards or rankings |
| Liquidity range | Explicitly advertised salary ranges, grouped by currency and pay period |
| Block stream | Requested skills from extracted posts, ordered by observed mention count |
| Activity feed | Source-linked Hacker News advertisements |
| Network and live indicator | Source range, last refresh, processed/remaining counts, and review or unavailable counts |

Use real Databricks-backed values only. Remove the reference's wallet data,
crypto terminology, hardcoded DEMO values, generated price walks, random
movement, live-accruing timers, and unsupported comparisons. Keep useful
interactions such as bringing a stacked major card forward, period controls,
and focus states. Motion must not make factual data move or hide content;
respect reduced-motion preferences and support keyboard and touch input.
Filters and coverage must remain visible without scrolling on desktop.

### Main views

- **Overview:** date, career, country, seniority, and remote-policy filters; demand and skills lead.
- **Careers:** software engineering, AI/ML, data science, data engineering, cybersecurity, and cloud/DevOps.
- **Compare majors:** up to three majors side by side, showing typical curriculum, prerequisites, career relevance, skill gaps, and sources.
- **Ask AI:** market questions, educational explanations, and supporting tables or charts.
- **Demo profiles:** save interests, favourite subjects, desired career, and shortlisted majors.
- **Source browser:** paginated advertisements with plain-text details and original HN links.

Use eight initial major subjects: Computer Science, Software Engineering, Computer Engineering, Data Science, Statistics, Mathematics, Cybersecurity, and Information Technology.

Use Impeccable’s operational-interface guidance, UI/UX Pro Max’s dashboard and
accessibility guidance, and GPT Taste’s typography and motion guidance within
this reference. The user selected a direct, code-first adaptation, so do not
replace the dashboard with a separate design concept or marketing page. Keep the
same composition while using precise student-facing copy and real evidence.

## 3. Backend, evidence, and AI

### Data and metrics

Read the existing `workspace.tech_careers.hn_job_posts` view. Default analytical queries to `extraction_status = 'ready'`, while exposing processing, review, failure, and exclusion counts separately.

- Count distinct advertisement IDs rather than claiming unique vacancies.
- Keep unknown values visible.
- Show gaps for unprocessed months and identify partially processed months.
- Avoid trend comparisons that imply incomplete periods are complete.
- Keep salary currencies and payment periods separate. Never assume annual pay.
- Treat skills and seniority as advertisement-level unions across roles.
- Create transparent career-family tags from explicit role-phrase matches. Label these as postings mentioning a career family, with overlapping categories allowed.

Cache aggregate responses for 60 seconds and provide manual refresh.

### API contracts

Provide endpoints for:

- Coverage, filters, overview metrics, and chart series.
- Paginated advertisements and source details.
- Careers, majors, and comparisons. Career families and curriculum content are
  currently curated in the frontend.
- Demo-profile creation, updates, selection, and deletion.
- Chat submission and status/results.

Use parameterized SQL, validated filters, bounded results, and server-side pagination. Frontend API types are currently local TypeScript definitions.

Store demo profiles in a dedicated Delta table. These are shared fictional demonstration profiles, not private student accounts.

### Educational guidance and chat

Create versioned educational content with verified official curriculum and career-resource links. Each pathway explains alternatives without numerical rankings or employment guarantees.

The workspace Genie space **Tech Career Market Explorer** exists. `app.yaml`
references the deployment resource key `genie-space`, rather than embedding its
workspace ID. A prior live request returned an answer and SQL, but no supporting
query rows. The app resource has not been assigned because the workspace
currently has no Databricks App for this project. Cloud deployment,
service-principal permissions, and result-row verification remain open.

Use one chat interface. The current endpoint calls Genie for market questions.
Routing educational questions to retrieved curriculum evidence and a
Databricks-hosted model remains a follow-up. Until then, the app presents
source-linked curriculum summaries directly.

Show generated SQL, supporting results, source links, execution identity, and AI limitations. Handle ambiguous questions, unavailable services, and quota failures explicitly. Keep chat history session-only.

## 4. Deployment, GitHub, and project context

### Databricks deployment

Use the app's service principal through Databricks SDK authentication and resource injection. Keep credentials server-side. `app.yaml` binds the warehouse and Genie space by resource key. `databricks.yml` defines least-privilege access to the warehouse (`CAN_USE`), Genie space (`CAN_RUN`), market tables (`SELECT`), and shared demo-profile table (`SELECT` and `MODIFY`). Databricks grants those permissions when the bundle is deployed; the deploying identity must be allowed to grant them. The demo-profile table already exists and passed a live save/select/delete check.

Build and stage the package with `python scripts/package_app.py`, then validate without deploying:

```powershell
databricks bundle validate --strict --target dev --var="warehouse_id=<free-warehouse-id>" --var="genie_space_id=<genie-space-id>" --profile tech-career
```

Strict validation passed for both `dev` and `prod`. Production resolves to the Databricks app identifier `tech-career-explorer`; the dashboard's visible name is CareerSync. The running app has its SQL warehouse, Genie space, and required Unity Catalog table resources attached. Anonymous visitors are redirected to Databricks sign-in. The workspace `users` group has `CAN_USE`, while the owner and admins retain `CAN_MANAGE`. Free Edition supports up to three Apps per account and automatically stops an App after 24 hours; users can restart it. Local live checks verified market data, profile persistence, and Genie answers with result rows. The deployed app startup and deployment state were verified through the CLI; a signed-in teammate browser walkthrough remains to be done. Preserve the existing extraction job and completion monitor.

### GitHub collaboration

The project has its own Git repository on `main`, separate from the Windows
profile repository.

The private remote is `William190811/tech-career-explorer`. Push the application,
ingestion code, tests, and documentation. Exclude downloaded data, credentials,
environments, build output, local caches, and the assignment PDF.

Add setup instructions, an environment-variable example containing no secrets, a contribution guide, and CI for frontend checks and backend tests. Document feature branches and pull requests.

Teammate invitations require their GitHub handles; do not infer recipients.

### Graphify and compressed handoff

- Configure Graphify for application code and architecture documentation, excluding raw datasets, dependencies, credentials, and generated inference artifacts.
- Generate the graph, report, and interactive HTML; run its integrity checks.
- Add project-scoped AGENTS integration and a local post-commit update hook.
- Document hook setup for teammates, since Git hooks are not transferred automatically.
- Create a compact project handoff note using Caveman Compress’s rules directly, preserving commands, paths, identifiers, and technical facts.
- Use no paid compression API and make no changes to global memories.

## 5. Verification and acceptance

Run focused checks for:

- Distinct-post counts, overlapping career tags, unknown values, incomplete periods, and salary grouping.
- Profile persistence and separation between named profiles.
- Filter/API consistency, pagination, empty results, and service errors.
- Genie numerical answers against known SQL results.
- Educational explanations against their cited sources.
- Dark theme, keyboard access, reduced motion, readable charts, and mobile layouts.
- The complete journey: choose a profile, explore a career, compare three majors, save a shortlist, ask a question, and inspect evidence.

For visual acceptance, compare a desktop capture at 1440px against the supplied
reference and inspect a 390px mobile capture. Confirm the four-column desktop
structure, major tile proportions and positions, stacked shortlist, dark
palette, lime highlight, lilac secondary accent, rounded panels, chart density,
and monospaced figures. Check that the first screen is recognizably the same
dashboard composition before judging polish. Mobile may reflow to one column,
but must retain the card stack, accent hierarchy, readable labels, and usable
chart controls. Fix material gaps together and confirm them in one final review.
Complete the Impeccable finish review and document the shipped design.

The 26 Python tests pass. The production frontend build and source compile pass;
lint passes without warnings. Browser checks with mocked API responses covered
filter requests, pagination, profile actions, dark-theme rendering, error recovery,
chart rendering, and Genie answer display. Live browser checks confirmed the
career filter changes hiring, trend, and skill metrics while archive coverage
stays global; a named demo profile can be saved, selected, and deleted; and a
Genie question renders its answer, generated SQL, and result rows. The filtered
market request took about 10 seconds on the updated backend in this check, though
runtime varies. The staged app's root and health endpoint also pass a local
request check. The build reports a 651.90 kB minified
JavaScript bundle, above Vite's advisory size threshold.

A live check of the Data scientist view returned 1,608 matching posts, refreshed
its chart and skill summaries, and populated the source feed. Selecting the
Software engineering demo profile changed the filtered count to 14,492. A raw
post containing a newline inside an encoded text field previously caused the
source feed to fail; the shared JSON parser now accepts that field, and the
regression test plus the live source feed pass.

The country dropdown previously stopped at 100 values. A read-only Genie One
query confirmed 141 distinct ready-post country values. Removing that cap makes
all 141 selectable; the live United States filter changed the headline count
from 38,615 to 10,701 posts.

Still open: a pre-existing local API process on port 8000 serves an older build;
development now uses port 8001. The latest dashboard read showed 43,450
processed input IDs, with 38,615 ready, 989 needing review, 1,157 non-hiring,
2,683 skipped as unavailable, and 6 failed. A live audit confirmed 43,450 rows,
43,450 distinct IDs, and no duplicate or null IDs. Four failures explicitly
report the Free Edition daily inference quota; two have only a generic
invalid-JSON diagnostic. The quota-blocked records cannot be retried until the
24-hour limit passes, and the two generic failures remain unresolved.
