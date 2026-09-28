"""Stream JSONL requests sequentially through one reusable SDK client."""

import argparse
import json
import sys
from contextlib import nullcontext

from common import DecisionError, create_client, decide, emit, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "requests", help="JSONL file: one {id, state, questions} record per line; - reads stdin"
    )
    args = parser.parse_args()
    failures = 0
    source = (
        nullcontext(sys.stdin)
        if args.requests == "-"
        else open(args.requests, encoding="utf-8-sig")
    )
    with source as lines, create_client() as client:
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            record_id = None
            try:
                record = json.loads(line)
                if not isinstance(record, dict) or set(record) != {"id", "state", "questions"}:
                    raise DecisionError(
                        "Each record must contain exactly id, state, and questions."
                    )
                if not isinstance(record["id"], str) or not record["id"]:
                    raise DecisionError("Each record needs a nonempty string id.")
                record_id = record.pop("id")
                result = decide(client, record)
                emit({"id": record_id, "line": line_number, "ok": True, "result": result})
            except (ValueError, DecisionError) as exc:
                failures += 1
                message = str(exc) if isinstance(exc, DecisionError) else "Invalid JSON record."
                emit({"id": record_id, "line": line_number, "ok": False, "error": message})
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run(main))
