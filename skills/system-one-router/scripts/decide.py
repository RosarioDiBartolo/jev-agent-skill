"""Evaluate one JSON request and write the typed response to stdout."""

import argparse

from common import create_client, decide, emit, load_json, run, validate_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="JSON file containing state and questions; - reads stdin")
    parser.add_argument(
        "--validate-only", action="store_true", help="validate locally without inference"
    )
    args = parser.parse_args()
    request = validate_request(load_json(args.request))
    if args.validate_only:
        emit({"valid": True, "questions": len(request["questions"])})
    else:
        with create_client() as client:
            emit(decide(client, request))


if __name__ == "__main__":
    raise SystemExit(run(main))
