// Node server for the perf dashboard (runs on the MacBook).
//
// - serves the built React dashboard (dist/)
// - automation API: create/list droplets (DigitalOcean), run scripts on the
//   droplet FastAPI server, run local post-processing, list run directories
//
// Env:
//   PORT        local port (default 3001)
//   DROPLET_API base URL of the droplet FastAPI server (default http://127.0.0.1:8000)
//   DO_TOKEN    DigitalOcean personal access token (for droplet creation)
//
// Dev: npm run dev  (vite on 5173 proxying /api -> 3001, node server on 3001)
// Prod: npm run build && npm start

import { execFile } from 'node:child_process'
import { readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import cors from 'cors'
import express from 'express'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')                 // /Users/dc/perf
const DIST = path.join(__dirname, 'dist')
const POSTPROCESS = path.join(ROOT, 'postprocess.py')

const PORT = process.env.PORT || 3001
const DROPLET_API = process.env.DROPLET_API || 'http://127.0.0.1:8000'
const DO_TOKEN = process.env.DO_TOKEN || ''
const DO_API = 'https://api.digitalocean.com/v2'

const app = express()
app.use(cors())
app.use(express.json({ limit: '2mb' }))

function run(cmd, args, cwd) {
  return new Promise((resolve) => {
    execFile(cmd, args, { cwd, timeout: 300000 }, (err, stdout, stderr) => {
      resolve({ ok: !err, code: err ? (err.code ?? 1) : 0, output: (stdout + '\n' + stderr).trim() })
    })
  })
}

// ---- status -------------------------------------------------------------
app.get('/api/health', (_req, res) => {
  res.json({ ok: true, node: process.version, root: ROOT, dropletApi: DROPLET_API, hasDoToken: !!DO_TOKEN })
})

// ---- local post-processing ---------------------------------------------
app.post('/api/postprocess', async (req, res) => {
  const runDir = req.body?.runDir ?? ''
  const args = runDir ? [runDir] : []
  res.json(await run('python3', [POSTPROCESS, ...args], ROOT))
})

// ---- results ------------------------------------------------------------
app.get('/api/profiles', (_req, res) => {
  const base = path.join(ROOT, 'profiles')
  let dirs = []
  try {
    dirs = readdirSync(base, { withFileTypes: true })
      .filter((d) => d.isDirectory() && d.name.startsWith('run_'))
      .sort((a, b) => (a.name < b.name ? 1 : -1))
      .map((d) => ({ dir: d.name, files: readdirSync(path.join(base, d.name)).sort() }))
  } catch {
    /* no profiles yet */
  }
  res.json({ dirs })
})

// ---- droplet automation (DigitalOcean API) ------------------------------
async function doFetch(pathname, init = {}) {
  if (!DO_TOKEN) throw new Error('DO_TOKEN is not set on the macos server')
  const res = await fetch(DO_API + pathname, {
    ...init,
    headers: { authorization: 'Bearer ' + DO_TOKEN, 'content-type': 'application/json', ...(init.headers ?? {}) },
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(JSON.stringify(body) ?? 'digitalocean HTTP ' + res.status)
  return body
}

app.post('/api/droplet/create', async (req, res) => {
  try {
    const { name = 'perf-runner', region = 'nyc3', size = 's-1vcpu-1gb', image = 'ubuntu-24-04-x64', sshKeys = [] } = req.body ?? {}
    const body = await doFetch('/droplets', {
      method: 'POST',
      body: JSON.stringify({ name, region, size, image, ssh_keys: sshKeys }),
    })
    res.json(body)
  } catch (e) {
    res.status(400).json({ error: String(e.message ?? e) })
  }
})

app.get('/api/droplet/list', async (_req, res) => {
  try {
    res.json(await doFetch('/droplets'))
  } catch (e) {
    res.status(400).json({ error: String(e.message ?? e) })
  }
})

app.get('/api/droplet/status/:id', async (req, res) => {
  try {
    res.json(await doFetch('/droplets/' + req.params.id))
  } catch (e) {
    res.status(400).json({ error: String(e.message ?? e) })
  }
})

// ---- forward script runs to the droplet FastAPI server ------------------
app.post('/api/droplet/run', async (req, res) => {
  try {
    const r = await fetch(DROPLET_API + '/api/run', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ script: req.body?.script ?? 'orig.py' }),
    })
    res.status(r.status).json(await r.json().catch(() => ({})))
  } catch (e) {
    res.status(502).json({ error: 'cannot reach droplet API at ' + DROPLET_API + ': ' + e.message })
  }
})

app.get('/api/droplet/run/:id', async (req, res) => {
  try {
    const r = await fetch(DROPLET_API + '/api/run/' + req.params.id)
    res.status(r.status).json(await r.json().catch(() => ({})))
  } catch (e) {
    res.status(502).json({ error: 'cannot reach droplet API at ' + DROPLET_API + ': ' + e.message })
  }
})

// ---- callback endpoint (droplet FastAPI -> dashboard) -------------------
app.post('/api/events/droplet-run-complete', (req, res) => {
  console.log('[droplet callback]', JSON.stringify(req.body ?? {}))
  res.json({ ok: true })
})

// ---- serve the built dashboard ------------------------------------------
app.use(express.static(DIST))
app.use((req, res, next) => {
  if (req.path.startsWith('/api')) return next()
  res.sendFile(path.join(DIST, 'index.html'))
})

app.listen(PORT, () => console.log('perf dashboard server on http://127.0.0.1:' + PORT))
