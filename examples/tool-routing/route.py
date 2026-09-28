"""Consume a decision file and propose a route; never execute a tool."""

import argparse
import json
import math


def propose(result, medium=None, high=None):
    answer = result["answers"]["tool"]
    tool, confidence = answer["choice"], answer["confidence"]
    allowed = {"gmail_search", "github_search", "web_search", "file_search"}
    route = "main_agent_review"
    if tool not in allowed:
        route = "main_agent_or_human"
    elif high is not None:
        if confidence >= high:
            route = "continue_with_authorized_tool"
        elif confidence < medium:
            route = "main_agent_or_human"
    return {
        "route": route,
        "proposed_tool": tool,
        "confidence": confidence,
        "probabilities": answer["probabilities"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response")
    parser.add_argument("--medium", type=float)
    parser.add_argument("--high", type=float)
    args = parser.parse_args()
    if (args.medium is None) != (args.high is None):
        parser.error("Supply both --medium and --high, or neither for review by default.")
    if args.high is not None and not (
        math.isfinite(args.medium)
        and math.isfinite(args.high)
        and 0 <= args.medium < args.high <= 1
    ):
        parser.error("Thresholds must satisfy 0 <= medium < high <= 1.")
    with open(args.response, encoding="utf-8-sig") as source:
        print(json.dumps(propose(json.load(source), args.medium, args.high)))


if __name__ == "__main__":
    main()
