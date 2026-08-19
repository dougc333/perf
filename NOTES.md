# droplet
cd /Users/dc/perf/droplet && uvicorn main:app --host 0.0.0.0 --port 8000

# macbook
cd /Users/dc/perf/macos
export DROPLET_API=http://<droplet-ip>:8000   # or use SSH tunnel: ssh -L 8000:127.0.0.1:8000 root@<droplet>
export DO_TOKEN=...                            # only needed for droplet creation
npm install && npm run build && npm start      # dashboard at http://127.0.0.1:3001
# or for development with hot reload: npm run dev
