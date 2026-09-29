import unittest
from unittest.mock import MagicMock, patch
import app

class TestHindsightLearningLoop(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    @patch("app.get_hindsight_client")
    def test_seed_memories_retains_all_incidents(self, mock_get_hs):
        """Verify seed_memories retains all 8 realistic incidents into Hindsight bank."""
        mock_hs = MagicMock()
        mock_get_hs.return_value = mock_hs

        with patch.dict("os.environ", {"HINDSIGHT_API_KEY": "test-key", "HINDSIGHT_BANK_ID": "recallops-demo"}):
            ok, msg = app.seed_memories()
            self.assertTrue(ok)
            self.assertIn("Successfully seeded 8 historical incidents", msg)
            # Verify create_bank was attempted
            mock_hs.create_bank.assert_called_once()
            # Verify retain was called 8 times
            self.assertEqual(mock_hs.retain.call_count, 8)
            # Verify first call had bank_id and tags
            first_call_kwargs = mock_hs.retain.call_args_list[0].kwargs
            self.assertEqual(first_call_kwargs["bank_id"], "recallops-demo")
            self.assertIn("payment-api", first_call_kwargs["tags"])

    @patch("app.get_llm_client")
    @patch("app.get_hindsight_client")
    def test_end_to_end_analyze_and_learning_loop(self, mock_get_hs, mock_get_llm):
        """
        Verify the complete workflow:
        1. Incident analyzed -> Hindsight recall called -> LLM analyzes with recalled memory
        2. Resolution saved -> Hindsight retain called
        3. Second incident analyzed -> recalls previous incident + newly learned resolution
        """
        mock_hs = MagicMock()
        mock_get_hs.return_value = mock_hs

        mock_llm = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""LIKELY CAUSE:
Database connection pool exhaustion after deployment.

CONFIDENCE:
High — Matches historical incident patterns in Payment API.

SIMILAR INCIDENTS:
2 previous payment incidents showed identical 503 and connection timeout patterns.

RECOMMENDED ACTIONS:
1. Check active database connections in PostgreSQL.
2. Inspect connection pool saturation metrics.
3. Compare configuration between v2.4.0 and v2.3.9.
4. Increase pool size and roll back if necessary.

WHY MEMORY HELPED:
Hindsight persistent memory retrieved verified precedent showing pool_size was set to 10 in deployment v2.4.0."""))
        ]
        mock_llm.chat.completions.create.return_value = mock_completion
        mock_get_llm.return_value = (mock_llm, "Groq", "llama-3.3-70b-versatile")

        # Mock recall response
        mock_recall_item = MagicMock()
        mock_recall_item.id = "MEM-001"
        mock_recall_item.text = "Incident INC-001: Payment API 503 errors caused by DB pool exhaustion."
        mock_recall_item.tags = ["payment-api", "database"]
        mock_recall_item.context = "Historical post-mortem"
        mock_recall_item.scores = {"relevance": 0.94}
        mock_recall_item.type = "historical_incident"

        mock_recall_response = MagicMock()
        mock_recall_response.results = [mock_recall_item]
        mock_hs.recall.return_value = mock_recall_response

        with patch.dict("os.environ", {"HINDSIGHT_API_KEY": "test-key", "GROQ_API_KEY": "test-groq"}):
            # Step 1: Submit Incident 1
            res = self.client.post("/analyze", json={
                "service": "Payment API",
                "environment": "Production",
                "error": "Payment API is returning 503 errors and database connection timeout messages after latest deployment."
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["ok"])
            self.assertEqual(len(data["memories"]), 1)
            self.assertIn("LIKELY CAUSE:", data["analysis"])
            self.assertIn("WHY MEMORY HELPED:", data["analysis"])

            # Step 2: Save Verified Resolution (Close the Learning Loop)
            incident_id = data["incident"]["id"]
            res_resolve = self.client.post("/resolve", json={
                "incident_id": incident_id,
                "service": "Payment API",
                "environment": "Production",
                "error": "Payment API 503 errors",
                "root_cause": "Database connection pool exhaustion after deployment",
                "resolution": "Increased PostgreSQL connection pool size to 80 and rolled back deployment."
            })
            self.assertEqual(res_resolve.status_code, 200)
            data_resolve = res_resolve.get_json()
            self.assertTrue(data_resolve["ok"])
            self.assertEqual(data_resolve["message"], "Resolution learned by Hindsight.")

            # Verify retain was called with verified resolution
            last_retain_call = mock_hs.retain.call_args.kwargs
            self.assertIn("verified-resolution", last_retain_call["tags"])
            self.assertIn("Verified Incident Post-Mortem & Resolution", last_retain_call["content"])

            # Step 3: Second incident with different wording
            # Mock recall returning the newly learned resolution!
            mock_learned_resolution = MagicMock()
            mock_learned_resolution.id = "MEM-LEARNED-01"
            mock_learned_resolution.text = f"Verified Resolution for Incident {incident_id} (Payment API): Root Cause: Database connection pool exhaustion. Resolution: Increased PostgreSQL pool size to 80."
            mock_learned_resolution.tags = ["payment-api", "verified-resolution", "learned-fix"]
            mock_learned_resolution.context = "Verified incident resolution"
            mock_learned_resolution.scores = {"relevance": 0.98}
            mock_learned_resolution.type = "verified_resolution"

            mock_hs.recall.return_value = MagicMock(results=[mock_learned_resolution, mock_recall_item])

            res2 = self.client.post("/analyze", json={
                "service": "Payment API",
                "environment": "Production",
                "error": "Customers are experiencing intermittent payment failures. The API is returning 503 responses and logs show database connection timeouts after release 2.4.1."
            })
            self.assertEqual(res2.status_code, 200)
            data2 = res2.get_json()
            self.assertTrue(data2["ok"])
            # Now 2 memories are recalled including the verified resolution!
            self.assertEqual(len(data2["memories"]), 2)
            self.assertIn("verified-resolution", data2["memories"][0]["tags"])

if __name__ == "__main__":
    unittest.main()
