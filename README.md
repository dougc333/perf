# perf

Profile how long it takes to import transformers and load a Hugging Face model
(Qwen/Qwen3-0.6B by default), using py-spy (https://github.com/benfred/py-spy)
sampling into speedscope (https://www.speedscope.app/) JSON.

## Install

    pip install -r requirements.txt   # runtime dependencies
    pip install -e .                  # optional: project + perf-* console scripts

## Usage

| Command | What it does |
| --- | --- |
| perf-measure | Wall-clock timings: import torch / import transformers / model load |
| perf-record | Same load under py-spy sampling -> hf_profile.speedscope.json |
| perf-speedgraph hf_profile.speedscope.json [-n 20] | Top frames by self / cumulative time |

The same scripts also run directly: python measure_2.py, python runme_droplet.py,
python speedgraph.py <file.json>.

## Notes

- py-spy attaches to the running process: Linux (root, as on the droplet) works
  directly; on macOS you may need elevated permissions. If attach fails, fall back
  to perf-measure for timings.
- Open the JSON in https://www.speedscope.app for the interactive flamegraph.
- hf_profile.speedscope.json / hf_profile.speedscope_coldstart.json are samples
  captured on the droplet.

## Sync runs from the droplet

run_and_sync.sh pushes the profiling scripts to the droplet, runs one of them
over SSH, then scp's the produced hf_profile*.json files back into a
timestamped directory under profiles/:

    export PERF_DROPLET=root@203.0.113.7   # your droplet (placeholder default)
    ./run_and_sync.sh                      # runs runme_droplet.py, then pulls JSONs
    ./run_and_sync.sh measure_2.py         # run a different script

Pulled files land in profiles/run_YYYYMMDD_HHMMSS/. Override locations with
PERF_DROPLET, PERF_REMOTE_DIR (default /root/perf) and PERF_PROFILES.

<!-- RESULTS:BEGIN -->

## Results

_Auto-updated by postprocess.py to the most recent run._

### Cold start

_placeholder: no cold-start snapshot yet_

### Warm start

_placeholder: no warm-start snapshot yet_

<!-- RESULTS:END -->
