"""Summarize OpenPortBench's paired exact/heuristic LNS experiments."""
import argparse
import json
from openportbench.analysis import summarize_file


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input_json")
    p.add_argument("--output", default=None)
    args = p.parse_args()
    r = summarize_file(args.input_json, args.output)
    print(json.dumps(r, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
