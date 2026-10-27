"""FastAPI backend for the single-process Databricks career explorer."""
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="CareerSync", version="0.1.0")
_market_cache = {}
CATALOG = os.getenv("HN_CATALOG", "workspace")
SCHEMA = os.getenv("HN_SCHEMA", "tech_careers")
POSTS = f"{CATALOG}.{SCHEMA}.hn_job_posts"
PROFILES = f"{CATALOG}.{SCHEMA}.student_demo_profiles"


def connection():
    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()
    warehouse = os.environ.get("DATABRICKS_WAREHOUSE_ID")
    if not warehouse:
        raise RuntimeError("Add a SQL warehouse resource to this Databricks app.")
    return sql.connect(server_hostname=cfg.host, http_path=f"/sql/1.0/warehouses/{warehouse}",
                       credentials_provider=lambda: cfg.authenticate)


def query(statement, params=None):
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(statement, params or [])
        if not cursor.description:
            return []
        keys = [col[0] for col in cursor.description]
        return [dict(zip(keys, row)) for row in cursor.fetchall()]


def query_batch(statements):
    """Run related reads over one warehouse connection to avoid repeated setup."""
    results = []
    with connection() as conn, conn.cursor() as cursor:
        for statement, params in statements:
            cursor.execute(statement, params or [])
            if not cursor.description:
                results.append([])
                continue
            keys = [col[0] for col in cursor.description]
            results.append([dict(zip(keys, row)) for row in cursor.fetchall()])
    return results


def as_json(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return json.loads(value, strict=False)


def service_error(context, exc):
    error = str(exc).lower()
    if any(marker in error for marker in ("free daily limit", "deny_new_and_existing_resources", "resource limit", "quota exceeded")):
        return "Databricks Free Edition has reached today's usage limit. Charts and shared profiles will return after the limit resets."
    return f"{context}: {exc}"


def filters_sql(filters):
    clauses = ["extraction_status = 'ready'", "is_hiring_ad = true"]
    params = []
    for key, column in (("career", "text_plain"), ("country", "country"),
                        ("remote", "remote_policy"), ("seniority", "seniority")):
        value = filters.get(key)
        if value:
            if key == "career":
                patterns = {"software engineer": ["%software engineer%", "%software developer%"],
                            "ai / ml engineer": ["%machine learning%", "%ai engineer%", "%ml engineer%"],
                            "data scientist": ["%data scientist%"], "data engineer": ["%data engineer%"],
                            "cybersecurity analyst": ["%cybersecurity%", "%security analyst%"],
                            "cloud / devops engineer": ["%devops%", "%cloud engineer%"]}.get(value.lower(), ["%" + value.lower() + "%"])
                clauses.append("(" + " OR ".join("lower(text_plain) LIKE ?" for _ in patterns) + ")")
                params.extend(patterns)
                continue
            elif key in ("country", "seniority"):
                clauses.append(f"array_contains({column}, ?)")
            else:
                clauses.append(f"{column} = ?")
            params.append(value)
    if filters.get("from"):
        clauses.append("month >= ?")
        params.append(filters["from"])
    if filters.get("to"):
        clauses.append("month <= ?")
        params.append(filters["to"])
    return " AND ".join(clauses), params


@app.get("/api/health")
def health():
    return {"status": "ok", "warehouse_configured": bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))}


@app.get("/api/whoami")
def whoami(request: Request):
    return {
        "user": request.headers.get("x-forwarded-email") or request.headers.get("x-forwarded-user"),
        "execution_identity": "Databricks app service principal" if os.getenv("DATABRICKS_CLIENT_ID") else "Local Databricks workspace identity",
    }


@app.get("/api/market")
def market(career: str | None = None, country: str | None = None, remote: str | None = None,
           seniority: str | None = None, start: str | None = None, end: str | None = None,
           refresh: int = 0):
    filters = {"career": career, "country": country, "remote": remote, "seniority": seniority,
               "from": start, "to": end}
    cache_key = tuple(filters.values())
    cached = _market_cache.get(cache_key)
    if not refresh and cached and time.monotonic() - cached[0] < 60:
        return cached[1]
    if len(_market_cache) >= 64:
        _market_cache.clear()
    where, params = filters_sql(filters)
    try:
        (counts, months, month_coverage, skills, remote_rows, countries, salaries,
         coverage, status_counts, options) = query_batch([
            (f"""SELECT COUNT(DISTINCT item_id) post_count,
          COUNT(DISTINCT CASE WHEN size(skills) > 0 THEN item_id END) skilled_posts,
          COUNT(DISTINCT CASE WHEN size(salary) > 0 THEN item_id END) salary_posts,
          COUNT(DISTINCT CASE WHEN remote_policy != 'not_stated' THEN item_id END) remote_stated,
          MIN(month) first_month, MAX(month) last_month
          FROM {POSTS} WHERE {where}""", params),
            (f"SELECT month, COUNT(DISTINCT item_id) posts FROM {POSTS} WHERE {where} GROUP BY month ORDER BY month", params),
            (f"""SELECT i.month, COUNT(DISTINCT i.item_id) source_posts, COUNT(DISTINCT p.item_id) processed_posts
          FROM {CATALOG}.{SCHEMA}.hn_extraction_inputs i
          LEFT JOIN {POSTS} p ON p.item_id=i.item_id
          GROUP BY i.month ORDER BY i.month""", []),
            (f"""SELECT skill, COUNT(DISTINCT item_id) mentions FROM {POSTS} LATERAL VIEW EXPLODE(skills) s AS skill
          WHERE {where} GROUP BY skill ORDER BY mentions DESC LIMIT 12""", params),
            (f"SELECT remote_policy, COUNT(DISTINCT item_id) posts FROM {POSTS} WHERE {where} GROUP BY remote_policy ORDER BY posts DESC", params),
            (f"""SELECT country_name country, COUNT(DISTINCT item_id) posts FROM {POSTS}
          LATERAL VIEW EXPLODE(country) c AS country_name WHERE {where}
          GROUP BY country_name ORDER BY posts DESC LIMIT 15""", params),
            (f"""SELECT s.currency, s.period, percentile_approx(s.minimum, .5) median_min,
          percentile_approx(s.maximum, .5) median_max, COUNT(DISTINCT item_id) offers
          FROM {POSTS} LATERAL VIEW EXPLODE(salary) x AS s WHERE {where} AND s.minimum IS NOT NULL
          GROUP BY s.currency, s.period ORDER BY offers DESC LIMIT 8""", params),
            (f"""SELECT (SELECT COUNT(DISTINCT item_id) FROM {CATALOG}.{SCHEMA}.hn_extraction_inputs) total,
          (SELECT COUNT(DISTINCT item_id) FROM {CATALOG}.{SCHEMA}.hn_extraction_validated) processed""", []),
            (f"SELECT extraction_status, COUNT(DISTINCT item_id) posts FROM {CATALOG}.{SCHEMA}.hn_extraction_validated GROUP BY extraction_status", []),
            (f"""SELECT DISTINCT country_name FROM {POSTS}
          LATERAL VIEW EXPLODE(country) c AS country_name WHERE extraction_status='ready' AND is_hiring_ad=true
          ORDER BY country_name""", []),
        ])
        result = {"summary": counts[0] if counts else {}, "coverage": coverage[0] if coverage else {}, "month_coverage": month_coverage, "months": months, "skills": skills,
                  "remote": remote_rows, "countries": countries, "salaries": salaries,
                  "statuses": {r["extraction_status"]: r["posts"] for r in status_counts},
                  "country_options": [r["country_name"] for r in options]}
        _market_cache[cache_key] = (time.monotonic(), result)
        return result
    except Exception as exc:
        raise HTTPException(503, service_error("Market data is not ready", exc)) from exc


@app.get("/api/posts")
def posts(career: str | None = None, country: str | None = None, remote: str | None = None,
          seniority: str | None = None, start: str | None = None, end: str | None = None,
          limit: int = 30, offset: int = 0):
    where, params = filters_sql({"career": career, "country": country, "remote": remote,
                                 "seniority": seniority, "from": start, "to": end})
    try:
        rows = query(f"""SELECT item_id, month, source_url, text_plain, skills, salary, seniority,
          country, remote_policy, extraction_status, validation_issues FROM {POSTS}
          WHERE {where} ORDER BY created_at_unix DESC LIMIT {max(1, min(limit, 100))} OFFSET {max(0, offset)}""", params)
        return [{**r, "skills": as_json(r["skills"]), "salary": as_json(r["salary"]),
                 "seniority": as_json(r["seniority"]), "country": as_json(r["country"]),
                 "validation_issues": as_json(r["validation_issues"])} for r in rows]
    except Exception as exc:
        raise HTTPException(503, service_error("Job posts are not ready", exc)) from exc


class Profile(BaseModel):
    name: str = Field(min_length=2, max_length=48)
    interests: list[str] = Field(default_factory=list, max_length=8)
    subjects: list[str] = Field(default_factory=list, max_length=8)
    career: str = ""
    majors: list[str] = Field(default_factory=list, max_length=3)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


@app.get("/api/profiles")
def list_profiles():
    try:
        rows = query(f"SELECT name, interests, subjects, career, majors FROM {PROFILES} ORDER BY name")
        return [{**row, "interests": as_json(row["interests"]) or [],
                 "subjects": as_json(row["subjects"]) or [], "career": row["career"] or "",
                 "majors": as_json(row["majors"]) or []} for row in rows]
    except Exception as exc:
        raise HTTPException(503, service_error("Demo profiles are not available", exc)) from exc


@app.put("/api/profiles")
def save_profile(profile: Profile):
    try:
        query(f"""MERGE INTO {PROFILES} AS t USING (SELECT ? name, from_json(?, 'ARRAY<STRING>') interests,
          from_json(?, 'ARRAY<STRING>') subjects, ? career, from_json(?, 'ARRAY<STRING>') majors) s
          ON lower(t.name)=lower(s.name)
          WHEN MATCHED THEN UPDATE SET interests=s.interests, subjects=s.subjects, career=s.career, majors=s.majors, updated_at=current_timestamp()
          WHEN NOT MATCHED THEN INSERT (name, interests, subjects, career, majors, updated_at)
          VALUES (s.name, s.interests, s.subjects, s.career, s.majors, current_timestamp())""",
              [profile.name.strip(), json.dumps(profile.interests), json.dumps(profile.subjects),
               profile.career, json.dumps(profile.majors)])
        return profile.model_dump()
    except Exception as exc:
        raise HTTPException(503, service_error("Could not save profile", exc)) from exc


@app.delete("/api/profiles/{name}")
def delete_profile(name: str):
    name = name.strip()
    if not 2 <= len(name) <= 48:
        raise HTTPException(422, "Profile names must be 2 to 48 characters.")
    try:
        query(f"DELETE FROM {PROFILES} WHERE lower(name)=lower(?)", [name])
        return {"deleted": name}
    except Exception as exc:
        raise HTTPException(503, service_error("Could not delete demo profile", exc)) from exc


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    conversation_id: str | None = None

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value):
        return value.strip() if isinstance(value, str) else value


@app.post("/api/chat")
def ask(question: Question):
    space_id = os.getenv("DATABRICKS_GENIE_SPACE_ID")
    if not space_id:
        raise HTTPException(503, "Genie is not connected yet. Add a Genie space resource to the app.")
    try:
        from databricks.sdk import WorkspaceClient
        client = WorkspaceClient()
        if question.conversation_id:
            response = client.genie.create_message_and_wait(space_id, question.conversation_id, question.question)
        else:
            response = client.genie.start_conversation_and_wait(space_id, question.question)
        message = getattr(response, "message", None) or response
        attachments = getattr(message, "attachments", None) or []
        answer = "\n\n".join(a.text.content for a in attachments if getattr(a, "text", None) and a.text.content)
        query_attachment = next((a for a in attachments if getattr(a, "query", None)), None)
        query = query_attachment.query if query_attachment else None
        query_results = None
        if query and getattr(message, "message_id", None) and getattr(query_attachment, "attachment_id", None):
            result_response = client.genie.get_message_attachment_query_result(
                space_id, message.conversation_id, message.message_id, query_attachment.attachment_id)
            statement = getattr(result_response, "statement_response", None)
            manifest = getattr(statement, "manifest", None)
            data = getattr(statement, "result", None)
            query_results = {
                "columns": [column.name or "" for column in (getattr(getattr(manifest, "schema", None), "columns", None) or [])],
                "rows": (getattr(data, "data_array", None) or [])[:10],
            }
        return {"conversation_id": getattr(message, "conversation_id", question.conversation_id),
                "answer": answer or "Genie returned no text answer. Review the generated query below.",
                "sql": query.query if query else None,
                "query_title": query.title if query else None,
                "query_results": query_results,
                "execution_identity": "Databricks app service principal" if os.getenv("DATABRICKS_CLIENT_ID") else "Local Databricks workspace identity"}
    except Exception as exc:
        raise HTTPException(502, f"Genie could not answer this question: {exc}") from exc


STATIC = Path(__file__).resolve().parent / "static"
if STATIC.exists():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="frontend")
