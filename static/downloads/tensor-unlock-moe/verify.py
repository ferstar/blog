#!/usr/bin/env python3
"""Recalculate the published numeric request summary, offline, with Python's standard library."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parent
EXPECTED_FIELDS = {
    "batch", "sample", "finish", "prompt_tokens", "prompt_read", "reused",
    "output_tokens", "engine_generated", "prompt_ms", "decode_ms", "decode_tok_s",
    "drafts_offered", "drafts_accepted",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, name):
    require(math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6),
            f"{name}: computed {actual!r}, expected {expected!r}")


def main():
    manifest = ROOT / "SHA256SUMS"
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            digest, name = line.split("  ", 1)
            require(Path(name).name == name, f"unexpected manifest path: {name}")
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            require(actual == digest, f"SHA-256 mismatch: {name}")
    summary = json.loads((ROOT / "summary.json").read_text())
    with (ROOT / "requests.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        require(set(reader.fieldnames or []) == EXPECTED_FIELDS, "unexpected CSV fields")
        rows = list(reader)
    require(len(rows) == summary["total_rows"], "total row count mismatch")
    require(set(r["batch"] for r in rows) == set(summary["batches"]), "batch set mismatch")
    results = {}
    for batch, expected in summary["batches"].items():
        group = [r for r in rows if r["batch"] == batch]
        require(len(group) == expected["requests"], f"{batch}: request count mismatch")
        require(len({r["sample"] for r in group}) == len(group), f"{batch}: duplicate sample")
        require(dict(Counter(r["finish"] for r in group)) == expected["finish"],
                f"{batch}: finish counts mismatch")
        require(all(r["finish"] == "stop" for r in group), f"{batch}: non-success row")
        for row in group:
            require(int(row["output_tokens"]) == int(row["engine_generated"]),
                    f"{batch}: API/native token mismatch")
            require(int(row["prompt_read"]) + int(row["reused"]) == int(row["prompt_tokens"]),
                    f"{batch}: prompt accounting mismatch")
            require(float(row["decode_ms"]) > 0 and float(row["prompt_ms"]) > 0,
                    f"{batch}: missing phase time")
        def total(key):
            return sum(float(r[key]) for r in group)
        for key in ["output_tokens", "prompt_ms", "decode_ms", "drafts_offered", "drafts_accepted"]:
            close(total(key), expected[key], batch + "." + key)
        close(total("prompt_read"), expected["fresh_prompt_tokens"], batch + ".fresh_prompt_tokens")
        close(total("reused"), expected["reused_prompt_tokens"], batch + ".reused_prompt_tokens")
        calculated = {
            "decode_weighted": total("output_tokens") / (total("decode_ms") / 1000),
            "decode_p50": statistics.median(float(r["decode_tok_s"]) for r in group),
            "prefill_weighted": total("prompt_read") / (total("prompt_ms") / 1000),
            "reuse_percent": 100 * total("reused") / total("prompt_tokens"),
            "mtp_acceptance_percent": 100 * total("drafts_accepted") / total("drafts_offered"),
            "input_at_least_65536": sum(int(r["prompt_tokens"]) >= 65536 for r in group),
        }
        for key, value in calculated.items():
            close(value, expected[key], batch + "." + key)
        results[batch] = {"requests": len(group), **calculated}
    print(json.dumps({"verified_rows": len(rows), "batches": results}, indent=2))


if __name__ == "__main__":
    main()
