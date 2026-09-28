"""Run a tiny inference probe (may incur provider cost)."""

import argparse
import time

from common import create_client, decide, emit, run


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    start = time.monotonic()
    with create_client() as client:
        result = decide(
            client,
            {
                "state": "The word is apple.",
                "questions": {"probe": {"type": "noul", "instructions": "Is the word apple?"}},
            },
        )
    emit(
        {
            "ok": True,
            "elapsed_ms": round((time.monotonic() - start) * 1000),
            "model": result["model"],
            "answers": result["answers"],
            "usage": result["usage"],
        }
    )


if __name__ == "__main__":
    raise SystemExit(run(main))
