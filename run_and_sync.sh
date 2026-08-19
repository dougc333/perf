#!/usr/bin/env bash
#
# run_and_sync.sh - run an HF profiling script on the droplet, then scp the
# produced speedscope JSON files back to this MacBook into a separate,
# timestamped directory, and post-process them into graph snapshots.
#
# Usage:
#   ./run_and_sync.sh [SCRIPT]        # default: runme_droplet.py
#
# Configuration (environment variables):
#   PERF_DROPLET     ssh target of the droplet, e.g. root@1.2.3.4 or an alias
#                    (default: root@203.0.113.7 - placeholder; the login
#                     procedure gets automated next, e.g. ssh key/agent)
#   PERF_REMOTE_DIR  directory on the droplet where the scripts run
#                    (default: /root/perf)
#   PERF_PROFILES    destination directory on this Mac
#                    (default: <this script's dir>/profiles)
#
# Examples:
#   PERF_DROPLET=root@203.0.113.7 ./run_and_sync.sh
#   ./run_and_sync.sh measure_2.py

set -euo pipefail

DROPLET="${PERF_DROPLET:-root@203.0.113.7}"
REMOTE_DIR="${PERF_REMOTE_DIR:-/root/perf}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILES_DIR="${PERF_PROFILES:-$HERE/profiles}"

SCRIPT="${1:-runme_droplet.py}"
SCRIPTS=(measure_2.py runme_droplet.py speedgraph.py)

echo "==> target: $DROPLET:$REMOTE_DIR (override with PERF_DROPLET / PERF_REMOTE_DIR)"

# 1. Keep the droplet copies of the profiling scripts up to date.
echo "==> copying scripts to $DROPLET:$REMOTE_DIR/"
scp "${SCRIPTS[@]}" "$DROPLET:$REMOTE_DIR/"

# 2. Run the profiling script on the droplet.
echo "==> running $SCRIPT on $DROPLET"
ssh "$DROPLET" "cd $REMOTE_DIR && python3 $SCRIPT"

# 3. Pull every JSON the run produced into a fresh, timestamped directory.
STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$PROFILES_DIR/run_$STAMP"
mkdir -p "$DEST"

echo "==> pulling hf_profile*.json from $DROPLET:$REMOTE_DIR into $DEST"
if scp "$DROPLET:$REMOTE_DIR/hf_profile*.json" "$DEST/" 2>/dev/null; then
    echo "==> pulled:"
    ls -1 "$DEST"
else
    echo "==> no hf_profile*.json found (script did not produce one)"
    rmdir "$DEST" 2>/dev/null || true
fi

# 4. Post-process on the MacBook: render flamegraph snapshots, update README.
if [ -f "$HERE/postprocess.py" ] && command -v python3 >/dev/null; then
    echo "==> post-processing $DEST (flamegraph snapshots + README update)"
    python3 "$HERE/postprocess.py" "$DEST"
fi
