import { useEffect, useRef, useState } from 'react'
import { dropletRun, dropletRunStatus } from '../api'
import type { RunInfo } from '../types'

export default function RunPanel() {
  const [script, setScript] = useState('orig.py')
  const [run, setRun] = useState<RunInfo | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const timer = useRef<number | null>(null)

  useEffect(() => () => { if (timer.current !== null) window.clearInterval(timer.current) }, [])

  async function start() {
    setBusy(true)
    setError('')
    setRun(null)
    try {
      const { run_id } = await dropletRun(script)
      poll(run_id)
    } catch (e) {
      setError(String(e))
      setBusy(false)
    }
  }

  function poll(id: string) {
    timer.current = window.setInterval(async () => {
      try {
        const info = await dropletRunStatus(id)
        setRun(info)
        if (info.status === 'done' || info.status === 'error') {
          if (timer.current !== null) window.clearInterval(timer.current)
          setBusy(false)
        }
      } catch (e) {
        setError(String(e))
        setBusy(false)
        if (timer.current !== null) window.clearInterval(timer.current)
      }
    }, 1500)
  }

  return (
    <section>
      <h2>Run a script on the droplet</h2>
      <div className="row">
        <input value={script} onChange={(e) => setScript(e.target.value)} placeholder="orig.py" />
        <button onClick={start} disabled={busy}>{busy ? 'running…' : 'Run'}</button>
      </div>
      <p className="hint">Calls the droplet FastAPI server (POST /api/run) through the macos server proxy.</p>
      {error !== '' && <pre className="error">{error}</pre>}
      {run !== null && (
        <div className="card">
          <p>
            run <b>{run.run_id}</b> · {run.script} · <b>{run.status}</b> · exit {run.exit_code ?? '…'}
          </p>
          {run.results.length > 0 && <p className="ok">produced: {run.results.join(', ')}</p>}
          <pre className="log">{run.output === '' ? '… waiting for output …' : run.output}</pre>
        </div>
      )}
    </section>
  )
}
