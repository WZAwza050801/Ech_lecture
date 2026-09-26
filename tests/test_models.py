import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from work.pipeline2.core import write_json
from work.pipeline2.models import Chat, check_json_strings, load_chat


class ModelTests(unittest.TestCase):
    def test_explicit_registry_beats_stale_generic_environment_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secrets.json"
            write_json(path, {"entries": [
                {"provider": "deepseek", "apiKey": "fixture-key",
                 "baseUrl": "https://api.deepseek.com", "models": ["deepseek-chat"]}]})
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "stale-fixture"}, clear=True):
                client = load_chat("text", path)
            self.assertEqual(client.api_key, "fixture-key")
            self.assertNotIn("fixture-key", repr(client))
            self.assertNotIn("fixture-key", json.dumps(client.identity))

    def test_invalid_math_json_gets_one_encoding_repair(self):
        outputs = [r'{"latex":"\lim_{x\to 0}x"}', json.dumps({"latex": r"\lim_{x\to 0}x"})]
        class Opener:
            calls = 0

            def open(self, request, timeout):
                output = outputs[self.calls]
                self.calls += 1
                data = {"choices": [{"finish_reason": "stop", "message": {"content": output}}]}
                return io.BytesIO(json.dumps(data).encode())
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            result = Chat("https://example.test", "fixture", "not-a-secret").json("JSON", {})
        self.assertEqual(result["latex"], r"\lim_{x\to 0}x")
        self.assertEqual(opener.calls, 2)

    def test_valid_json_cannot_silently_corrupt_math_escapes(self):
        for raw in [r'{"latex":"\frac{x}{y}"}', r'{"latex":"\nabla f"}', r'{"symbol":"\theta"}']:
            with self.assertRaises(ValueError):
                check_json_strings(json.loads(raw))

    def test_network_timeout_reports_original_error_not_unbound_local(self):
        """Regression: the OSError/TimeoutError handler used {error} without binding it."""
        class Opener:
            def open(self, request, timeout):
                raise TimeoutError("The read operation timed out")
        with patch("urllib.request.build_opener", return_value=Opener()), \
                patch.dict(os.environ, {"ECHONOTES_MODEL_RETRIES": "1"}, clear=True):
            with self.assertRaises(RuntimeError) as caught:
                Chat("https://example.test", "fixture", "not-a-secret").json("JSON", {})
        message = str(caught.exception)
        self.assertIn("The read operation timed out", message)
        self.assertIn("ECHONOTES_MODEL_TIMEOUT", message)

    def test_http_error_keeps_truncated_provider_message(self):
        """Regression: the HTTPError handler dropped the server error body."""
        class Opener:
            def open(self, request, timeout):
                body = json.dumps({"error": {"message": "Not found the model kimi-k3 or Permission denied"}})
                raise urllib.error.HTTPError("https://example.test", 404, "Not Found", {},
                                             io.BytesIO(body.encode()))
        with patch("urllib.request.build_opener", return_value=Opener()), \
                patch.dict(os.environ, {"ECHONOTES_MODEL_RETRIES": "2"}, clear=True):
            with self.assertRaises(RuntimeError) as caught:
                Chat("https://example.test", "fixture", "not-a-secret").json("JSON", {})
        message = str(caught.exception)
        self.assertIn("HTTP 404", message)
        self.assertIn("Not found the model kimi-k3", message)


if __name__ == "__main__":
    unittest.main()
