#!/usr/bin/env python3
"""Chap. 16 — golden-set regression gate.

Scores a GGUF candidate against a frozen golden set and blocks promotion
(exit 1) when pass-rate drops more than --threshold points under baseline.

Usage:
    python eval_gate.py --golden golden.jsonl --gguf assistant.gguf \
        --baseline results/baseline.json --threshold 2

First successful run with no baseline file becomes the baseline.
"""

import argparse
import datetime
import json
from pathlib import Path


def check(output: str, task: dict) -> bool:
    """Deterministic check: reference string must appear in the answer."""
    return str(task["reference"]).lower() in output.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="golden.jsonl")
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--baseline", default="results/baseline.json")
    ap.add_argument(
        "--threshold", type=float, default=2.0, help="max allowed drop, points"
    )
    ap.add_argument(
        "--adapter-out", default=None, help=argparse.SUPPRESS
    )  # finetune_unsloth.py compat
    args = ap.parse_args()

    from llama_cpp import Llama  # type: ignore[import-not-found]

    tasks = []
    try:
        with open(args.golden) as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"[gate] cannot read golden set {args.golden}: {e}") from e
    llm = Llama(model_path=args.gguf, n_ctx=4096, verbose=False)

    passed = 0
    for t in tasks:
        out = llm.create_chat_completion(
            messages=[{"role": "user", "content": t["instruction"]}],
            max_tokens=512,
            temperature=0.0,
        )
        if check(out["choices"][0]["message"]["content"], t):
            passed += 1

    score = round(100 * passed / len(tasks), 2)
    result = {
        "date": datetime.datetime.now().isoformat(timespec="seconds"),
        "gguf": args.gguf,
        "golden_size": len(tasks),
        "pass_rate": score,
    }
    print(f"[gate] pass@1 = {score}% ({passed}/{len(tasks)})")

    base = Path(args.baseline)
    if base.exists():
        try:
            baseline = json.loads(base.read_text())["pass_rate"]
        except (OSError, json.JSONDecodeError, KeyError) as e:
            raise SystemExit(f"[gate] unreadable baseline {base}: {e}") from e
        result["baseline"] = baseline
        if score < baseline - args.threshold:
            Path("results").mkdir(exist_ok=True)
            (base.parent / f"failed-{result['date'].replace(':', '')}.json").write_text(
                json.dumps(result, indent=2)
            )
            sys_exit(f"{score}% < baseline {baseline}% − {args.threshold} → BLOCKED")
    else:
        Path(args.baseline).parent.mkdir(parents=True, exist_ok=True)
        base.write_text(json.dumps(result, indent=2))
        print(f"[gate] no baseline existed — recorded this run ({score}%)")

    print(f"[gate] OK → {json.dumps(result)}")


def sys_exit(msg):
    raise SystemExit(f"[gate] FAIL — {msg}")


if __name__ == "__main__":
    main()
