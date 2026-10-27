# Graph Report - Mockup Software Design  (2026-10-27)

## Corpus Check
- 30 files · ~17,898 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 273 nodes · 338 edges · 20 communities (13 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ec27665f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- App.tsx
- package.json
- DashboardApiTests
- app.py
- ingest_hn.py
- benchmark_hn_models.py
- compilerOptions
- CareerSync user and test guide
- compilerOptions
- CareerSync implementation
- Model comparison
- .oxlintrc.json
- AI extraction pilot: first 20 HN posts
- tsconfig.json
- Full archive extraction
- AGENTS.md
- package_app.py
- extract_hn_sample.py

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 18 edges
2. `DashboardApiTests` - 18 edges
3. `compilerOptions` - 15 edges
4. `App()` - 12 edges
5. `CareerSync user and test guide` - 10 edges
6. `ValidationTests` - 8 edges
7. `query()` - 7 edges
8. `FilterSqlTests` - 7 edges
9. `Model comparison` - 7 edges
10. `CareerSync implementation` - 6 edges

## Surprising Connections (you probably didn't know these)
- `run()` --calls--> `align_evidence()`  [EXTRACTED]
  scripts/benchmark_hn_models.py → scripts/validate_hn_extraction.py

## Import Cycles
- None detected.

## Communities (20 total, 5 thin omitted)

### Community 0 - "App.tsx"
Cohesion: 0.08
Nodes (26): App(), ask(), removeProfile(), saveProfile(), careers, getRead(), Identity, majorColors (+18 more)

### Community 1 - "package.json"
Cohesion: 0.06
Nodes (36): dependencies, lucide-react, react, react-dom, recharts, devDependencies, oxlint, tailwindcss (+28 more)

### Community 3 - "app.py"
Cohesion: 0.14
Nodes (25): as_json(), ask(), connection(), delete_profile(), filters_sql(), health(), list_profiles(), market() (+17 more)

### Community 4 - "ingest_hn.py"
Cohesion: 0.38
Nodes (10): cli(), download(), download_thread(), get(), load(), month_key(), official(), Download monthly HN hiring posts and merge raw records into Databricks. (+2 more)

### Community 5 - "benchmark_hn_models.py"
Cohesion: 0.17
Nodes (9): Resumable archive extraction on serverless compute; no schedule or paid…, expression(), model_sql(), Compare workspace models on the same reviewed 20-post sample., run(), align_evidence(), Source-grounded checks shared by benchmarking and archive processing., validate() (+1 more)

### Community 6 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 7 - "CareerSync user and test guide"
Cohesion: 0.11
Nodes (17): CareerSync, Codebase map, Project map, Quick start for students, Run locally, Automated checks, Career and subject exploration, CareerSync user and test guide (+9 more)

### Community 8 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 9 - "CareerSync implementation"
Cohesion: 0.14
Nodes (14): 1. Outcome and architecture, 2. Interface and student experience, 3. Backend, evidence, and AI, 4. Deployment, GitHub, and project context, 5. Verification and acceptance, API contracts, CareerSync implementation, Data and metrics (+6 more)

### Community 11 - "Model comparison"
Cohesion: 0.25
Nodes (7): ai_extract_precision, Model comparison, system.ai.gpt-oss-120b, system.ai.gpt-oss-20b, system.ai.meta-llama-3-3-70b-instruct, system.ai.qwen35-122b-a10b, system.ai.qwen3-next-80b-a3b-instruct

### Community 12 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 13 - "AI extraction pilot: first 20 HN posts"
Cohesion: 0.33
Nodes (5): AI extraction pilot: first 20 HN posts, Limits, Results, Stored outputs, Verification

### Community 20 - "extract_hn_sample.py"
Cohesion: 0.31
Nodes (7): check(), evaluate(), literal(), query(), Materialize and inspect a fixed 20-post Databricks ai_extract pilot., run(), Deploy and launch the selected-model archive extraction inside Databricks.

## Knowledge Gaps
- **117 isolated node(s):** `Project guidance`, `1. Outcome and architecture`, `Visual direction: follow the supplied dashboard closely`, `Main views`, `Data and metrics` (+112 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 167 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Project guidance`, `1. Outcome and architecture`, `Visual direction: follow the supplied dashboard closely` to the rest of the system?**
  _117 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.0761904761904762 - nodes in this community are weakly interconnected._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05547652916073969 - nodes in this community are weakly interconnected._
- **Should `DashboardApiTests` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13756613756613756 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `CareerSync user and test guide` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._