"""Summarize a speedscope sampled profile (e.g. py-spy output) from the CLI.

Usage:
    python speedgraph.py hf_profile.speedscope.json [-n 20]
    (or the installed console script: perf-speedgraph hf_profile.speedscope.json [-n 20])

Prints the top frames by self and cumulative time. Works with the sampled
profile format that 'py-spy record --format speedscope' emits; open the JSON
in https://www.speedscope.app for the interactive flamegraph.
"""

import argparse
import json
import sys

UNIT_TO_SECONDS = {
    "seconds": 1.0,
    "milliseconds": 1e-3,
    "microseconds": 1e-6,
    "nanoseconds": 1e-9,
}


def _iter_samples(profile):
    samples = profile.get("samples", [])
    weights = profile.get("weights")
    if weights is None or len(weights) != len(samples):
        weights = [1] * len(samples)
        count_only = True
    else:
        scale = UNIT_TO_SECONDS.get(profile.get("unit", "seconds"))
        count_only = scale is None
        if not count_only:
            weights = [w * scale for w in weights]
    return samples, weights, count_only


def summarize(path: str, top_n: int) -> None:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read {path}: {exc}")

    frames = data.get("shared", {}).get("frames", [])
    profiles = data.get("profiles") or []
    if not profiles:
        sys.exit(f"{path}: no profiles found")

    n_frames = len(frames)

    for profile in profiles:
        name = profile.get("name", "profile")
        if profile.get("type") != "sampled":
            print(f"[{name}] skipped (type={profile.get('type')}, expected 'sampled')")
            continue

        samples, weights, count_only = _iter_samples(profile)
        if not samples:
            print(f"[{name}] no samples")
            continue

        self_time = [0.0] * n_frames
        cum_time = [0.0] * n_frames
        total = 0.0
        for sample, weight in zip(samples, weights):
            total += weight
            if not sample:
                continue
            if sample[-1] < n_frames:
                self_time[sample[-1]] += weight
            for frame in sample:
                if frame < n_frames:
                    cum_time[frame] += weight

        if total <= 0:
            print(f"[{name}] zero total time")
            continue

        def fmt(value: float) -> str:
            if count_only:
                return f"{value:>10.0f} samples"
            return f"{value:>9.3f}s ({100 * value / total:5.1f}%)"

        print()
        print(f"[{name}] {len(samples)} samples, total {fmt(total)}")

        def top(values, label):
            print()
            print(f"Top {top_n} by {label} time:")
            shown = 0
            for frame_idx in sorted(range(n_frames), key=lambda i: values[i], reverse=True):
                if values[frame_idx] <= 0:
                    break
                shown += 1
                if shown > top_n:
                    break
                meta = frames[frame_idx]
                where = meta.get("file") or ""
                if meta.get("line") is not None:
                    where = f"{where}:{meta['line']}"
                print(f"{shown:>3}. {fmt(values[frame_idx])}  {meta.get('name', '?')}  [{where}]")
            if shown == 0:
                print("   (none)")

        top(self_time, "self")
        top(cum_time, "cumulative")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "profile", nargs="?", default="hf_profile.speedscope.json",
        help="path to a speedscope JSON file (default: hf_profile.speedscope.json)",
    )
    parser.add_argument("-n", "--top", type=int, default=20,
                        help="how many frames to show (default: 20)")
    args = parser.parse_args()
    summarize(args.profile, args.top)


if __name__ == "__main__":
    main()
