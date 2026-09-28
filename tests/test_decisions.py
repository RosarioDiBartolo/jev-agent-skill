import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import httpx2
from typesafe_sdk import RetryPolicy, TypeSafeClient

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/system-one-router/scripts"
sys.path.insert(0, str(SCRIPTS))
import common  # noqa: E402


def reply(request):
    answers = {}
    for name, q in request["questions"].items():
        if q["type"] == "noul":
            answers[name] = {"type": "noul", "noul": 0.9}
        else:
            keys = (
                list(q["criteria"])
                if q["type"] == "choice"
                else [str(i) for i in range(len(q["criteria"]))]
            )
            answer = {
                "type": q["type"],
                "confidence": 1.0,
                "probabilities": {k: float(i == 0) for i, k in enumerate(keys)},
            }
            if q["type"] == "choice":
                answer["choice"] = keys[0]
            else:
                answer.update(score=0.0, legend=dict(zip(keys, q["criteria"])))
            answers[name] = answer
    return {
        "model": "test-model",
        "answers": answers,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT / "examples/email-triage/request.json").read_text())

    def client(self, handler):
        return TypeSafeClient(
            api_key="test-only",
            base_url="http://test.invalid/prefix",
            model="test-model",
            retry=RetryPolicy(max_retries=0),
            transport=httpx2.MockTransport(handler),
        )

    def test_all_primitives_use_custom_endpoint_and_keep_values(self):
        captured = []

        def handler(request):
            captured.append(request)
            return httpx2.Response(200, json=reply(json.loads(request.content)))

        with self.client(handler) as client:
            result = common.decide(client, self.request)
        self.assertEqual(str(captured[0].url), "http://test.invalid/prefix/v1/systemone")
        self.assertEqual(captured[0].headers["authorization"], "Bearer test-only")
        self.assertEqual(json.loads(captured[0].content)["model"], "test-model")
        self.assertEqual(result["answers"]["requires_reply"], {"type": "noul", "noul": 0.9})
        self.assertEqual(
            result["answers"]["urgency"]["probabilities"], {"0": 1.0, "1": 0.0, "2": 0.0}
        )
        self.assertEqual(result["usage"]["input_tokens"], 10)

    def test_errors_do_not_expose_backend_body(self):
        for status in (401, 403, 404, 422, 429, 500, 529):
            with self.subTest(status=status):
                with self.client(
                    lambda _: httpx2.Response(status, json={"error": "secret-private-state"})
                ) as client:
                    with self.assertRaises(common.DecisionError) as caught:
                        common.decide(client, self.request)
                self.assertNotIn("secret-private-state", str(caught.exception))

    def test_timeout_has_safe_error(self):
        def handler(request):
            raise httpx2.ReadTimeout("secret-private-state", request=request)

        with self.client(handler) as client:
            with self.assertRaisesRegex(common.DecisionError, "reachability"):
                common.decide(client, self.request)

    def test_malformed_and_mismatched_answers_fail(self):
        good = reply(self.request)
        missing = copy.deepcopy(good)
        del missing["answers"]["urgency"]
        wrong_type = copy.deepcopy(good)
        wrong_type["answers"]["category"] = {"type": "noul", "noul": 0.8}
        wrong_options = copy.deepcopy(good)
        wrong_options["answers"]["category"].update(
            choice="unknown", probabilities={"unknown": 1.0}
        )
        invalid = copy.deepcopy(good)
        invalid["answers"]["requires_reply"]["noul"] = 1.5
        for data in ({}, missing, wrong_type, wrong_options, invalid):
            with self.subTest(data=data):
                with self.client(lambda _: httpx2.Response(200, json=data)) as client:
                    with self.assertRaises(common.DecisionError):
                        common.decide(client, self.request)

    def test_bad_input_rejected_before_network(self):
        invalids = [
            None,
            {},
            {"state": 5, "questions": {}},
            {"state": "x", "questions": {}, "model": "accidental"},
            {
                "state": "x",
                "questions": {"a": {"type": "score", "instructions": "rate", "criteria": ["one"]}},
            },
        ]
        for value in invalids:
            with self.subTest(value=value), self.assertRaises(common.DecisionError):
                common.validate_request(value)

    def test_no_implicit_hosted_fallback(self):
        with patch.dict(
            os.environ,
            {"TYPESAFE_API_KEY": "unrelated", "TYPESAFE_BASE_URL": "https://api.typesafe.ai"},
            clear=True,
        ):
            with self.assertRaisesRegex(common.DecisionError, "SYSTEM_ONE_BASE_URL"):
                common.create_client()

    def test_configuration_validation(self):
        env = {
            "SYSTEM_ONE_BASE_URL": "http://localhost:8009",
            "SYSTEM_ONE_API_KEY": "test-only",
            "SYSTEM_ONE_MODEL": "kev-latest",
        }
        bad = [
            ("BASE_URL", "http://localhost:8009/v1"),
            ("BASE_URL", "https://user:secret@example.com"),
            ("BASE_URL", "https://example.com?key=secret"),
            ("BASE_URL", "file:///tmp/x"),
            ("TIMEOUT", "nan"),
            ("TIMEOUT", "0"),
            ("MAX_RETRIES", "6"),
            ("MAX_RETRIES", "1.5"),
        ]
        for key, value in bad:
            with self.subTest(key=key, value=value):
                with patch.dict(os.environ, {**env, "SYSTEM_ONE_" + key: value}, clear=True):
                    with self.assertRaises(common.DecisionError):
                        common.create_client()

    def test_examples_validate(self):
        for path in (ROOT / "examples").glob("*/request.json"):
            common.validate_request(common.load_json(str(path)))


class CLIIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                cls.requests.append((self.path, request))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(reply(request)).encode())

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def invoke(self, script, *args, stdin=None):
        env = {
            **os.environ,
            "SYSTEM_ONE_BASE_URL": f"http://127.0.0.1:{self.server.server_port}",
            "SYSTEM_ONE_API_KEY": "test-only",
            "SYSTEM_ONE_MODEL": "kev-latest",
            "SYSTEM_ONE_MAX_RETRIES": "0",
            "SYSTEM_ONE_TIMEOUT": "5",
            "NO_PROXY": "127.0.0.1,localhost",
            "TYPESAFE_LOG_LEVEL": "error",
        }
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            input=stdin,
            text=True,
            capture_output=True,
            env=env,
            cwd=tempfile.gettempdir(),
            timeout=20,
        )

    def test_decide_from_other_directory(self):
        result = self.invoke("decide.py", str(ROOT / "examples/tool-routing/request.json"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["answers"]["tool"]["choice"], "gmail_search")
        self.assertEqual(self.requests[-1][0], "/v1/systemone")

    def test_stdin_and_validation_only_do_not_infer(self):
        before = len(self.requests)
        request = (ROOT / "examples/classification/request.json").read_text()
        result = self.invoke("decide.py", "-", "--validate-only", stdin=request)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])
        self.assertEqual(len(self.requests), before)

    def test_health_really_runs_inference(self):
        result = self.invoke("health.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertIn("probe", self.requests[-1][1]["questions"])

    def test_batch_partial_failure_preserves_order_and_ids(self):
        request = json.loads((ROOT / "examples/classification/request.json").read_text())
        record = {"id": "issue-1", **request}
        lines = json.dumps(record) + "\nnot-json\n\n" + json.dumps({**record, "id": "issue-2"})
        result = self.invoke("batch_decide.py", "-", stdin=lines)
        self.assertEqual(result.returncode, 1)
        output = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([r["ok"] for r in output], [True, False, True])
        self.assertEqual([r["line"] for r in output], [1, 2, 4])
        self.assertEqual([r["id"] for r in output], ["issue-1", None, "issue-2"])

    def test_batch_example_runs(self):
        result = self.invoke("batch_decide.py", str(ROOT / "examples/email-triage/records.jsonl"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 3)

    def test_bad_json_has_no_traceback(self):
        result = self.invoke("decide.py", "-", stdin="private-state-not-json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("private-state", result.stderr)
        self.assertIn("error", json.loads(result.stderr))


class RoutingPolicyTests(unittest.TestCase):
    def test_review_default_and_three_threshold_paths(self):
        spec = importlib.util.spec_from_file_location(
            "route_example", ROOT / "examples/tool-routing/route.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = reply(json.loads((ROOT / "examples/tool-routing/request.json").read_text()))
        self.assertEqual(module.propose(data)["route"], "main_agent_review")
        for confidence, expected in (
            (0.95, "continue_with_authorized_tool"),
            (0.7, "main_agent_review"),
            (0.3, "main_agent_or_human"),
        ):
            data["answers"]["tool"]["confidence"] = confidence
            self.assertEqual(module.propose(data, 0.5, 0.9)["route"], expected)
        data["answers"]["tool"].update(choice="unavailable-tool", confidence=1.0)
        self.assertEqual(module.propose(data, 0.5, 0.9)["route"], "main_agent_or_human")


if __name__ == "__main__":
    unittest.main()
