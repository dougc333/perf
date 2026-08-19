import { useEffect, useState } from 'react'
import { listProfiles } from '../api'

export default function ResultsPanel() {
  const [dirs, setDirs] = useState<{ dir: string; files: string[] }[]>([])
  const [err, setErr] = useState('')

  useEffect(() => {
    listProfiles().then((r) => setDirs(r.dirs)).catch((e) => setErr(String(e)))
  }, [])

  return (
    <section>
      <h2>Results (profiles/run_*)</h2>
      {err !== '' && <pre className="error">{err}</pre>}
      {dirs.length === 0 && <p className="hint">no run directories yet — run a sync or postprocess first.</p>}
      {dirs.map((d) => (
        <div key={d.dir} className="card">
          <h3>{d.dir}</h3>
          <ul>{d.files.map((f) => <li key={f}>{f}</li>)}</ul>
        </div>
      ))}
    </section>
  )
}
