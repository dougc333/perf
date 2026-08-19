# droplet - FastAPI runner server

Runs the profiling scripts (orig.py etc.) on the droplet. The MacBook dashboard
talks to this server to start runs and fetch their output.

## Run

    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000

Interactive API docs: http://<droplet-ip>:8000/docs

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /health | status + available scripts |
| GET | /api/scripts | list runnable .py scripts |
| POST | /api/run | start a run: {"script": "orig.py", "args": []} -> {run_id} |
| POST | /api/run/orig | start orig.py |
| GET | /api/run/{run_id} | run status + captured output |
| GET | /api/runs | list recent runs |
| GET | /api/results | list produced hf_profile*.json files |

## Callback to the dashboard

Set CALLBACK_URL so completed runs POST back to the macos server:

    CALLBACK_URL=http://<macos-ip>:3001/api/events/droplet-run-complete uvicorn main:app --host 0.0.0.0 --port 8000

## Firewall

Allow inbound 8000/tcp so the dashboard can reach it:

    ufw allow 8000/tcp
