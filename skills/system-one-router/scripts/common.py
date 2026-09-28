"""Small execution adapter around the official TypeSafe SDK."""

import json
import math
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit


class DecisionError(Exception):
    """A safe, actionable error that contains no request or response body."""


def load_json(path):
    try:
        text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")
        return json.loads(text, parse_constant=lambda _: _invalid_json())
    except (OSError, UnicodeError, ValueError) as exc:
        raise DecisionError("Cannot read JSON input; check the file path and JSON syntax.") from exc


def _invalid_json():
    raise ValueError("Non-finite JSON number")


def emit(value, stream=None):
    print(
        json.dumps(value, ensure_ascii=True, allow_nan=False), file=stream or sys.stdout, flush=True
    )


def validate_request(request):
    if not isinstance(request, dict) or set(request) != {"state", "questions"}:
        raise DecisionError(
            "Request must contain exactly state and questions; configure model in the environment."
        )
    if not isinstance(request["state"], (str, dict, list)):
        raise DecisionError("state must be a string, object, or array.")
    questions = request["questions"]
    if not isinstance(questions, dict) or not questions:
        raise DecisionError("questions must be a nonempty object.")
    for name, question in questions.items():
        if not isinstance(name, str) or not name or not isinstance(question, dict):
            raise DecisionError("Each question needs a nonempty ID and an object value.")
        if set(question) - {"type", "instructions", "criteria"}:
            raise DecisionError("Unknown question field; use type, instructions, and criteria.")
        if not isinstance(question.get("instructions"), (str, dict, list)):
            raise DecisionError("Every question needs instructions as a string, object, or array.")
        kind, criteria = question.get("type"), question.get("criteria")
        if kind == "choice":
            if not isinstance(criteria, dict) or not 2 <= len(criteria) <= 255:
                raise DecisionError(
                    "Choice criteria must map 2..255 options to descriptions or null."
                )
        elif kind == "score":
            if not isinstance(criteria, list) or not 2 <= len(criteria) <= 10:
                raise DecisionError("Score criteria must contain 2..10 ordered level descriptions.")
        elif kind == "noul":
            if criteria is not None and (
                not isinstance(criteria, dict) or set(criteria) - {"true", "false"}
            ):
                raise DecisionError("Noul criteria may contain only true and false descriptions.")
        else:
            raise DecisionError("Question type must be choice, noul, or score.")
    try:
        json.dumps(request, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise DecisionError("Request must contain finite JSON values.") from exc
    return request


def create_client():
    config = {
        key: os.environ.get("SYSTEM_ONE_" + key, "").strip()
        for key in ("BASE_URL", "API_KEY", "MODEL")
    }
    missing = ["SYSTEM_ONE_" + key for key, value in config.items() if not value]
    if missing:
        raise DecisionError("Set " + ", ".join(missing) + "; no hosted-service fallback is used.")
    try:
        url = urlsplit(config["BASE_URL"])
        valid = (
            url.scheme in {"http", "https"}
            and url.hostname
            and not (url.username or url.password or url.query or url.fragment)
        )
        if not valid or url.path.rstrip("/").endswith(("/v1", "/v1/systemone")):
            raise ValueError()
        _ = url.port
    except ValueError as exc:
        raise DecisionError(
            "SYSTEM_ONE_BASE_URL must be an HTTP(S) API root without credentials, query, /v1, or /v1/systemone."
        ) from exc
    try:
        timeout = float(os.environ.get("SYSTEM_ONE_TIMEOUT", "30"))
        retries = int(os.environ.get("SYSTEM_ONE_MAX_RETRIES", "0"))
        if not math.isfinite(timeout) or timeout <= 0 or not 0 <= retries <= 5:
            raise ValueError()
    except ValueError as exc:
        raise DecisionError(
            "TIMEOUT must be positive and finite; MAX_RETRIES must be an integer from 0 to 5."
        ) from exc
    try:
        from typesafe_sdk import RetryPolicy, TypeSafeClient
    except ImportError as exc:
        raise DecisionError(
            "Install this skill's requirements.txt with the Python interpreter used to run the scripts."
        ) from exc
    try:
        return TypeSafeClient(
            api_key=config["API_KEY"],
            base_url=config["BASE_URL"].rstrip("/"),
            model=config["MODEL"],
            timeout=timeout,
            retry=RetryPolicy(max_retries=retries),
        )
    except Exception as exc:
        raise DecisionError(
            "SDK configuration failed; check the API key format and installed SDK version."
        ) from exc


def decide(client, request):
    validate_request(request)
    try:
        response = client.system_one(state=request["state"], questions=request["questions"])
        data = response.model_dump(mode="json")
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        hints = {
            401: "Authentication failed; check SYSTEM_ONE_API_KEY and server authentication.",
            403: "Access denied; check endpoint or tunnel access rules.",
            404: "Endpoint or model not found; check API root and model name.",
            422: "Backend rejected the request; check questions and backend compatibility.",
            429: "Rate limited; reduce request rate or configure bounded retries.",
            529: "Backend overloaded; retry later.",
        }
        raise DecisionError(
            hints.get(
                status,
                "Decision call failed; check server reachability, timeout, model, and API compatibility.",
            )
        ) from exc
    answers = data.get("answers", {})
    if set(answers) != set(request["questions"]):
        raise DecisionError("Backend returned missing or unexpected question IDs.")
    for name, question in request["questions"].items():
        answer = answers[name]
        if answer.get("type") != question["type"]:
            raise DecisionError("Backend returned a mismatched answer type.")
        if question["type"] == "noul":
            check_number(answer.get("noul"), 0, 1)
        else:
            check_number(answer.get("confidence"), 0, 1)
            probabilities = answer.get("probabilities", {})
            for probability in probabilities.values():
                check_number(probability, 0, 1)
            if not probabilities or abs(sum(probabilities.values()) - 1) >= 0.02:
                raise DecisionError("Backend returned probabilities that do not sum to one.")
        if question["type"] == "choice":
            expected = set(question["criteria"])
            if (
                set(answer.get("probabilities", {})) != expected
                or answer.get("choice") not in expected
            ):
                raise DecisionError("Backend returned options outside the requested choice set.")
        if question["type"] == "score":
            expected = {str(i) for i in range(len(question["criteria"]))}
            if (
                set(answer.get("probabilities", {})) != expected
                or set(answer.get("legend", {})) != expected
            ):
                raise DecisionError("Backend returned unexpected score levels.")
            check_number(answer.get("score"), 0, len(expected) - 1)
    return data


def check_number(value, minimum, maximum):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not minimum <= value <= maximum
    ):
        raise DecisionError("Backend returned a non-finite or out-of-range numeric answer.")


def run(main):
    try:
        return main() or 0
    except DecisionError as exc:
        emit({"error": str(exc)}, sys.stderr)
        return 1
    except (OSError, UnicodeError):
        emit({"error": "Unable to read or write a file or stream."}, sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
