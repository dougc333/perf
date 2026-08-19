import { useState } from 'react'
import { runPostprocess } from '../api'

export default function PostProcessPanel() {
  const [runDir, setRunDir] = useState('')
  const [output, setOutput] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  async function go() {
    setBusy(true)
    setErr('')
    setOutput('')
    try {
      const r = await runPostprocess(runDir === '' ? undefined : runDir)
      setOutput(r.output)
    } catch (e) {
      setErr(String(e))
    }
    setBusy(false)
  }

  return (
    <section>
      <h2>Post-process (runs on this Mac)</h2>
      <div className="row">
        <input
          value={runDir}
          onChange={(e) => setRunDir(e.target.value)}
          placeholder="run dir (default: latest profiles/run_*)"
        />
        <button onClick={go} disabled={busy}>{busy ? 'running…' : 'Run postprocess'}</button>
      </div>
      <p className="hint">Runs postprocess.py: flamegraph snapshots + README results update.</p>
      {err !== '' && <pre className="error">{err}</pre>}
      {output !== '' && <pre className="log">{output}</pre>}
    </section>
  )
}
