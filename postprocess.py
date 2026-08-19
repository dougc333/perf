"""Post-process speedscope JSON profiles pulled from the droplet (runs on the MacBook).

For a run directory containing hf_profile*.json files:
  1. renders each JSON as a speedscope-style flamegraph SVG (stdlib only),
  2. converts each SVG to a PNG screenshot (headless Chrome, else qlmanage),
  3. optionally captures a screenshot of the real speedscope.app via Playwright,
  4. updates the README "Results" section to point at the most recent
     cold-start and warm-start snapshots.

Usage:
    python3 postprocess.py [RUN_DIR] [--no-readme]

RUN_DIR defaults to the newest profiles/run_* directory under this repo.
"""

import argparse
import base64
import html
import json
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROW_H = 18          # px per stack row
TOP = 8             # px before the first row
BOTTOM = 28         # px reserved for the footer
WIDTH = 1600        # svg width
MAX_DEPTH = 60      # cap rendered stack depth (README-sized snapshots)

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]

UNIT_SCALE = {"seconds": 1.0, "milliseconds": 1e-3, "microseconds": 1e-6, "nanoseconds": 1e-9}


def find_chrome():
    for cand in CHROME_CANDIDATES:
        path = shutil.which(cand) if "/" not in cand else cand
        if path and Path(path).exists():
            return path
    return None


def load_sampled(path):
    """Return (frames, samples, weights_in_seconds) of the busiest sampled profile."""
    data = json.loads(path.read_text())
    frames = data["shared"]["frames"]
    sampled = [p for p in data.get("profiles", []) if p.get("type") == "sampled"]
    if not sampled:
        raise ValueError(f"{path.name}: no sampled profile")
    profile = max(sampled, key=lambda p: len(p.get("samples", [])))
    samples = profile.get("samples", [])
    weights = profile.get("weights")
    scale = UNIT_SCALE.get(profile.get("unit", "seconds"), 1.0)
    if weights is None or len(weights) != len(samples):
        weights = [1.0] * len(samples)
    return frames, samples, [w * scale for w in weights]


def merge_runs(samples, weights):
    """Collapse consecutive identical stacks (classic flamegraph optimization)."""
    merged = []  # (stack, duration)
    for sample, weight in zip(samples, weights):
        if merged and merged[-1][0] == sample:
            merged[-1][1] += weight
        else:
            merged.append([sample, weight])
    return merged


def render_flamegraph_svg(json_path, out_svg):
    frames, samples, weights = load_sampled(json_path)
    if not samples:
        print(f"  {json_path.name}: no samples, skipping")
        return None
    runs = merge_runs(samples, weights)
    total = sum(w for _, w in runs)
    max_depth = min(max((len(s) for s, _ in runs), default=0), MAX_DEPTH)
    capped = max_depth >= MAX_DEPTH
    height = TOP + max_depth * ROW_H + BOTTOM

    hue = [0] * len(frames)
    for i, frame in enumerate(frames):
        h = 0
        for ch in frame.get("name", "?"):
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        hue[i] = h % 360

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
        f'<rect x="0" y="0" width="{WIDTH}" height="{height}" fill="#ffffff"/>',
    ]
    x = 0.0
    for stack, duration in runs:
        w = max(0.5, duration / total * WIDTH)
        x0, x1 = x, x + w
        for depth, fi in enumerate(stack[:MAX_DEPTH]):
            y = TOP + depth * ROW_H
            name = frames[fi].get("name", "?") if fi < len(frames) else "?"
            fill = f"hsl({hue[fi] if fi < len(frames) else 0},55%,62%)"
            parts.append(f'<rect x="{x0:.2f}" y="{y}" width="{w:.2f}" height="{ROW_H - 2}" fill="{fill}" rx="1"/>')
            if w > 60:
                label = name if len(name) * 6.2 < w - 8 else name[:max(1, int((w - 8) / 6.2))]
                parts.append(f'<text x="{x0 + 4:.2f}" y="{y + 13}" font-family="Menlo, monospace" font-size="11">{html.escape(label)}</text>')
        x = x1
    note = " (top {} rows shown)".format(MAX_DEPTH) if capped else ""
    parts.append(
        f'<text x="8" y="{height - 8}" font-family="Menlo, monospace" font-size="11" fill="#333">'
        f'{html.escape(json_path.stem)} - {len(samples)} samples, {total:.3f}s{note}</text>'
    )
    parts.append("</svg>")
    out_svg.write_text("\n".join(parts))
    return height


def svg_to_png(svg_path, out_png):
    chrome = find_chrome()
    if chrome is not None:
        try:
            subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 f"--window-size={WIDTH},1200", f"--screenshot={out_png}",
                 svg_path.resolve().as_uri()],
                check=True, timeout=90,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if out_png.exists():
                return f"chrome -> {out_png.name}"
        except Exception:
            pass
    try:
        ql = subprocess.run(
            ["qlmanage", "-t", "-s", "1600", "-o", str(svg_path.parent), str(svg_path)],
            timeout=90, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        produced = svg_path.parent / (svg_path.name + ".png")
        if ql.returncode == 0 and produced.exists():
            produced.rename(out_png)
            return f"qlmanage -> {out_png.name}"
    except Exception:
        pass
    return None


def speedscope_screenshot(json_path, out_png):
    """Screenshot of the real speedscope.app via Playwright (optional dependency)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "playwright not installed (pip install playwright && playwright install chromium)"
    try:
        data_url = "data:application/json;base64," + base64.b64encode(json_path.read_bytes()).decode()
        target = "https://www.speedscope.app/#profileURL=" + urllib.parse.quote(data_url, safe="")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            page.goto(target, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(12000)  # give speedscope time to load + render
            page.screenshot(path=str(out_png))
            browser.close()
        return f"speedscope -> {out_png.name}"
    except Exception as exc:
        return f"speedscope screenshot failed: {exc}"


README_BEGIN = "<!-- RESULTS:BEGIN -->"
README_END = "<!-- RESULTS:END -->"


def update_readme(readme: Path, run_dir: Path, cold: "Path | None", warm: "Path | None"):
    text = readme.read_text()

    def rel(p):
        try:
            return p.relative_to(readme.parent).as_posix()
        except ValueError:
            return p.as_posix()

    def img(p):
        return rel(p) if p is not None and p.exists() else None

    cold_img, warm_img = img(cold), img(warm)
    lines = [
        README_BEGIN, "",
        "## Results", "",
        "_Auto-updated by postprocess.py to the most recent run._", "",
        "### Cold start", "",
    ]
    lines += [f"![cold start flamegraph]({cold_img})" if cold_img
              else "_placeholder: no cold-start snapshot yet_", ""]
    lines += ["### Warm start", ""]
    lines += [f"![warm start flamegraph]({warm_img})" if warm_img
              else "_placeholder: no warm-start snapshot yet_", "", README_END]
    block = "\n".join(lines)

    if README_BEGIN in text and README_END in text:
        head, _, tail = text.partition(README_BEGIN)
        _, _, rest = tail.partition(README_END)
        text = head + block + rest
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    readme.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", default=None,
                        help="run directory with hf_profile*.json (default: newest profiles/run_*)")
    parser.add_argument("--no-readme", action="store_true", help="do not update README.md")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    if args.run_dir:
        run_dir = Path(args.run_dir).resolve()
    else:
        profiles = here / "profiles"
        candidates = sorted(profiles.glob("run_*")) if profiles.exists() else []
        if not candidates:
            sys.exit("no profiles/run_* directory found; pass a run directory explicitly")
        run_dir = candidates[-1]

    jsons = sorted(run_dir.glob("hf_profile*.json"))
    if not jsons:
        sys.exit(f"{run_dir}: no hf_profile*.json files found")

    cold = [p for p in jsons if "coldstart" in p.name]
    warm = [p for p in jsons if "coldstart" not in p.name]
    print(f"post-processing {run_dir}")

    cold_png = warm_png = None
    for group, label in ((warm, "warm"), (cold, "cold")):
        for json_path in group:
            print(f"  [{label}] {json_path.name}")
            svg = run_dir / (json_path.stem + ".flamegraph.svg")
            height = render_flamegraph_svg(json_path, svg)
            if height is None:
                continue
            print(f"    wrote {svg.name} ({svg.stat().st_size} bytes, {height}px tall)")
            png = run_dir / (json_path.stem + ".png")
            result = svg_to_png(svg, png)
            print(f"    screenshot: {result or 'no PNG renderer available (install Chrome, or qlmanage failed)'}")
            if group is warm:
                warm_png = png
            if group is cold:
                cold_png = png
            sshot = run_dir / (json_path.stem + ".speedscope.png")
            print(f"    speedscope: {speedscope_screenshot(json_path, sshot)}")

    if not args.no_readme:
        readme = here / "README.md"
        update_readme(readme, run_dir, cold_png, warm_png)
        print(f"updated {readme.name}")


if __name__ == "__main__":
    main()
