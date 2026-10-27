import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app as dashboard


class FilterSqlTests(unittest.TestCase):
    def test_as_json_handles_newlines_inside_encoded_text_fields(self):
        parsed = dashboard.as_json('[{"raw_text":"S\nenior Web Security Engineer"}]')
        self.assertEqual(parsed, [{"raw_text": "S\nenior Web Security Engineer"}])

    def test_query_batch_reuses_one_connection(self):
        cursor = unittest.mock.MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.description = [("value",)]
        cursor.fetchall.side_effect = [[(1,)], [(2,)]]
        conn = unittest.mock.MagicMock()
        conn.__enter__.return_value = conn
        conn.cursor.return_value = cursor
        with patch.object(dashboard, "connection", return_value=conn) as connect:
            result = dashboard.query_batch([("SELECT 1", []), ("SELECT 2", [])])
        connect.assert_called_once_with()
        self.assertEqual(cursor.execute.call_count, 2)
        self.assertEqual(result, [[{"value": 1}], [{"value": 2}]])

    def test_all_filter_placeholders_match_parameters(self):
        sql, params = dashboard.filters_sql({
            "career": "Data scientist",
            "country": "Canada",
            "remote": "remote",
            "seniority": "senior",
            "from": "2024-01",
            "to": "2026-10",
        })
        self.assertEqual(sql.count("?"), len(params))
        self.assertEqual(params, ["%data scientist%", "Canada", "remote", "senior", "2024-01", "2026-10"])

    def test_software_career_uses_both_keywords_without_an_extra_parameter(self):
        sql, params = dashboard.filters_sql({"career": "Software engineer"})
        self.assertIn("lower(text_plain) LIKE ? OR lower(text_plain) LIKE ?", sql)
        self.assertEqual(params, ["%software engineer%", "%software developer%"])
        self.assertEqual(sql.count("?"), len(params))

    def test_every_career_family_expands_to_its_expected_role_phrases(self):
        careers = {
            "Software engineer": ["%software engineer%", "%software developer%"],
            "AI / ML engineer": ["%machine learning%", "%ai engineer%", "%ml engineer%"],
            "Data scientist": ["%data scientist%"],
            "Data engineer": ["%data engineer%"],
            "Cybersecurity analyst": ["%cybersecurity%", "%security analyst%"],
            "Cloud / DevOps engineer": ["%devops%", "%cloud engineer%"],
        }
        for career, expected in careers.items():
            with self.subTest(career=career):
                sql, params = dashboard.filters_sql({"career": career})
                self.assertEqual(params, expected)
                self.assertEqual(sql.count("?"), len(params))

    def test_filter_values_remain_bound_parameters(self):
        injected = "Canada' OR 1=1 --"
        sql, params = dashboard.filters_sql({"country": injected})
        self.assertNotIn(injected, sql)
        self.assertEqual(params, [injected])


class DashboardApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(dashboard.app)
        dashboard._market_cache.clear()
        self.query_patch = patch.object(dashboard, "query")
        self.query = self.query_patch.start()
        self.addCleanup(self.query_patch.stop)
        self.query_batch_patch = patch.object(dashboard, "query_batch")
        self.query_batch = self.query_batch_patch.start()
        self.addCleanup(self.query_batch_patch.stop)
        self.addCleanup(self.client.close)

    def market_query(self, sql, params=None):
        if "COUNT(DISTINCT CASE" in sql:
            return [{"post_count": 4, "skilled_posts": 3, "salary_posts": 1,
                     "remote_stated": 2, "first_month": "2024-01", "last_month": "2026-10"}]
        if "SELECT month, COUNT(DISTINCT item_id) posts" in sql:
            return [{"month": "2024-01", "posts": 4}]
        if "hn_extraction_inputs i" in sql:
            return [{"month": "2024-01", "source_posts": 5, "processed_posts": 4}]
        if "EXPLODE(skills)" in sql:
            return [{"skill": "Python", "mentions": 3}]
        if "remote_policy, COUNT" in sql:
            return [{"remote_policy": "remote", "posts": 2}]
        if "EXPLODE(country)" in sql and "SELECT DISTINCT" not in sql:
            return [{"country": "Canada", "posts": 2}]
        if "percentile_approx" in sql:
            return [{"currency": "CAD", "period": "year", "median_min": 100000,
                     "median_max": 140000, "offers": 1}]
        if "hn_extraction_inputs) total" in sql:
            return [{"total": 10, "processed": 8}]
        if "GROUP BY extraction_status" in sql:
            return [{"extraction_status": "ready", "posts": 8},
                    {"extraction_status": "needs_review", "posts": 1}]
        if "SELECT DISTINCT country_name" in sql:
            return [{"country_name": f"Country {index}"} for index in range(141)]
        return []

    def market_batch(self, statements):
        return [self.market_query(sql, params) for sql, params in statements]

    def test_health_reports_configuration_and_whoami_uses_forwarded_identity(self):
        with patch.dict(os.environ, {"DATABRICKS_WAREHOUSE_ID": "warehouse"}):
            self.assertEqual(self.client.get("/api/health").json(), {"status": "ok", "warehouse_configured": True})
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.client.get("/api/health").json(), {"status": "ok", "warehouse_configured": False})
        response = self.client.get("/api/whoami", headers={"x-forwarded-email": "student@example.test"})
        self.assertEqual(response.json()["user"], "student@example.test")
        self.assertEqual(response.json()["execution_identity"], "Local Databricks workspace identity")
        with patch.dict(os.environ, {"DATABRICKS_CLIENT_ID": "app-client"}):
            response = self.client.get("/api/whoami", headers={"x-forwarded-user": "student-user"})
        self.assertEqual(response.json()["user"], "student-user")
        self.assertEqual(response.json()["execution_identity"], "Databricks app service principal")

    def test_market_applies_all_selected_filters_to_metrics_and_keeps_coverage_global(self):
        self.query_batch.side_effect = self.market_batch
        response = self.client.get("/api/market", params={
            "career": "Data scientist", "country": "Canada", "remote": "remote",
            "seniority": "senior", "start": "2024-01", "end": "2026-10",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["post_count"], 4)
        self.assertEqual(data["months"][0]["posts"], 4)
        self.assertEqual(data["skills"][0]["skill"], "Python")
        self.assertEqual(data["remote"][0]["posts"], 2)
        self.assertEqual(data["coverage"], {"total": 10, "processed": 8})
        self.assertEqual(data["statuses"]["needs_review"], 1)

        queries = self.query_batch.call_args.args[0]
        filtered = [(sql, params or []) for sql, params in queries
                    if "FROM workspace.tech_careers.hn_job_posts" in sql
                    and "SELECT DISTINCT country_name" not in sql]
        self.assertEqual(len(filtered), 6)
        for sql, params in filtered:
            self.assertEqual(sql.count("?"), len(params))
            self.assertIn("2024-01", params)
            self.assertIn("2026-10", params)
            self.assertIn("Canada", params)
            self.assertIn("remote", params)
            self.assertIn("senior", params)
        global_queries = [(sql, params or []) for sql, params in queries
                          if "hn_extraction_inputs i" in sql or "hn_extraction_inputs) total" in sql
                          or "GROUP BY extraction_status" in sql]
        self.assertTrue(global_queries)
        self.assertTrue(all(not params for _, params in global_queries))

    def test_market_cache_is_filter_specific_and_refresh_bypasses_it(self):
        self.query_batch.side_effect = self.market_batch
        self.client.get("/api/market", params={"career": "Data scientist"})
        call_count = self.query_batch.call_count
        self.client.get("/api/market", params={"career": "Data scientist"})
        self.assertEqual(self.query_batch.call_count, call_count)
        self.client.get("/api/market", params={"career": "Software engineer"})
        self.assertGreater(self.query_batch.call_count, call_count)
        call_count = self.query_batch.call_count
        self.client.get("/api/market", params={"career": "Data scientist", "refresh": 1})
        self.assertGreater(self.query_batch.call_count, call_count)

    def test_market_returns_all_country_filter_options(self):
        self.query_batch.side_effect = self.market_batch
        response = self.client.get("/api/market")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["country_options"]), 141)
        options_sql = next(sql for sql, _ in self.query_batch.call_args.args[0]
                           if "SELECT DISTINCT country_name" in sql)
        self.assertNotIn("LIMIT", options_sql)

    def test_posts_binds_filters_decodes_json_and_bounds_pagination(self):
        self.query.return_value = [{"item_id": 123, "skills": '["Python"]', "salary": "[]",
                                    "seniority": "[]", "country": '["Canada"]',
                                    "validation_issues": "[]"}]
        response = self.client.get("/api/posts", params={"career": "Software engineer", "limit": 999, "offset": -4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["skills"], ["Python"])
        sql, params = self.query.call_args.args
        self.assertIn("LIMIT 100 OFFSET 0", sql)
        self.assertEqual(sql.count("?"), len(params))

    def test_profiles_list_save_validation_and_delete(self):
        self.query.return_value = []
        self.assertEqual(self.client.get("/api/profiles").json(), [])
        saved = self.client.put("/api/profiles", json={"name": "  Data path  ", "career": "Data scientist",
                                                        "majors": ["Data science"], "interests": [], "subjects": []})
        self.assertEqual(saved.status_code, 200)
        sql, params = self.query.call_args.args
        self.assertIn("MERGE INTO workspace.tech_careers.student_demo_profiles", sql)
        self.assertEqual(params[0], "Data path")
        self.assertEqual(saved.json()["name"], "Data path")
        self.assertEqual(self.client.put("/api/profiles", json={"name": "x"}).status_code, 422)
        self.assertEqual(self.client.put("/api/profiles", json={"name": "   "}).status_code, 422)
        self.assertEqual(self.client.put("/api/profiles", json={"name": "Too many", "majors": ["a", "b", "c", "d"]}).status_code, 422)
        self.assertEqual(self.client.delete("/api/profiles/x").status_code, 422)
        deleted = self.client.delete("/api/profiles/Data%20path")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json(), {"deleted": "Data path"})

    def test_profile_list_decodes_json_arrays_and_defaults_null_fields(self):
        self.query.return_value = [
            {"name": "Saved path", "interests": '["AI / ML engineer"]',
             "subjects": '["Computer science"]', "career": "AI / ML engineer",
             "majors": '["Computer science"]'},
            {"name": "Empty path", "interests": None, "subjects": None,
             "career": None, "majors": None},
        ]
        response = self.client.get("/api/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["interests"], ["AI / ML engineer"])
        self.assertEqual(response.json()[0]["subjects"], ["Computer science"])
        self.assertEqual(response.json()[0]["majors"], ["Computer science"])
        self.assertEqual(response.json()[1]["interests"], [])
        self.assertEqual(response.json()[1]["subjects"], [])
        self.assertEqual(response.json()[1]["majors"], [])
        self.assertEqual(response.json()[1]["career"], "")

    def test_chat_starts_and_continues_genie_conversations_and_returns_results(self):
        columns = [SimpleNamespace(name="skill")]
        message = SimpleNamespace(
            conversation_id="conversation-1", message_id="message-1",
            attachments=[SimpleNamespace(attachment_id="attachment-1",
                                          text=SimpleNamespace(content="Python is common."),
                                          query=SimpleNamespace(query="SELECT skill", title="Skills"))],
        )
        client = SimpleNamespace(genie=SimpleNamespace(
            start_conversation_and_wait=unittest.mock.Mock(return_value=SimpleNamespace(message=message)),
            create_message_and_wait=unittest.mock.Mock(return_value=SimpleNamespace(message=message)),
            get_message_attachment_query_result=unittest.mock.Mock(return_value=SimpleNamespace(
                statement_response=SimpleNamespace(
                    manifest=SimpleNamespace(schema=SimpleNamespace(columns=columns)),
                    result=SimpleNamespace(data_array=[["Python"]]),
                ),
            )),
        ))
        with patch.dict(os.environ, {"DATABRICKS_GENIE_SPACE_ID": "space-1"}), \
                patch("databricks.sdk.WorkspaceClient", return_value=client):
            started = self.client.post("/api/chat", json={"question": "  What skills are popular?  "})
            continued = self.client.post("/api/chat", json={"question": "And in remote roles?",
                                                             "conversation_id": "conversation-1"})
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.json()["answer"], "Python is common.")
        client.genie.start_conversation_and_wait.assert_called_once_with("space-1", "What skills are popular?")
        self.assertEqual(started.json()["query_results"]["rows"], [["Python"]])
        client.genie.get_message_attachment_query_result.assert_has_calls([
            unittest.mock.call("space-1", "conversation-1", "message-1", "attachment-1"),
            unittest.mock.call("space-1", "conversation-1", "message-1", "attachment-1"),
        ])
        self.assertEqual(continued.status_code, 200)
        client.genie.start_conversation_and_wait.assert_called_once()
        client.genie.create_message_and_wait.assert_called_once()

    def test_chat_without_space_and_invalid_question_return_clear_errors(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DATABRICKS_GENIE_SPACE_ID", None)
            missing = self.client.post("/api/chat", json={"question": "What jobs?"})
        self.assertEqual(missing.status_code, 503)
        self.assertIn("Genie is not connected", missing.json()["detail"])
        self.assertEqual(self.client.post("/api/chat", json={"question": "?"}).status_code, 422)
        self.assertEqual(self.client.post("/api/chat", json={"question": "   "}).status_code, 422)

    def test_chat_workspace_errors_are_returned_as_gateway_errors(self):
        client = SimpleNamespace(genie=SimpleNamespace(
            start_conversation_and_wait=unittest.mock.Mock(side_effect=RuntimeError("Genie unavailable")),
        ))
        with patch.dict(os.environ, {"DATABRICKS_GENIE_SPACE_ID": "space-1"}), \
                patch("databricks.sdk.WorkspaceClient", return_value=client):
            response = self.client.post("/api/chat", json={"question": "What skills are popular?"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("Genie unavailable", response.json()["detail"])

    def test_market_and_posts_surface_database_errors_as_service_unavailable(self):
        self.query_batch.side_effect = RuntimeError("free daily limit exceeded")
        self.query.side_effect = RuntimeError("free daily limit exceeded")
        self.assertEqual(self.client.get("/api/market").status_code, 503)
        self.assertIn("usage limit", self.client.get("/api/market", params={"refresh": 1}).json()["detail"])
        self.assertEqual(self.client.get("/api/posts").status_code, 503)

    def test_free_resource_quota_error_has_a_clear_message_for_profiles(self):
        self.query.side_effect = RuntimeError("DENY_NEW_AND_EXISTING_RESOURCES")
        response = self.client.get("/api/profiles")
        self.assertEqual(response.status_code, 503)
        self.assertIn("usage limit", response.json()["detail"])

    def test_profile_write_errors_are_reported_without_success(self):
        self.query.side_effect = RuntimeError("warehouse unavailable")
        response = self.client.put("/api/profiles", json={"name": "Class demo"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("Could not save profile", response.json()["detail"])

    def test_profile_delete_errors_are_reported_without_success(self):
        self.query.side_effect = RuntimeError("warehouse unavailable")
        response = self.client.delete("/api/profiles/Class%20demo")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Could not delete demo profile", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
