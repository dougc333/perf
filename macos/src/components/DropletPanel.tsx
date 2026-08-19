import { useEffect, useState } from 'react'
import { dropletCreate, dropletList } from '../api'
import type { DropletSummary } from '../types'

export default function DropletPanel() {
  const [name, setName] = useState('perf-runner')
  const [region, setRegion] = useState('nyc3')
  const [size, setSize] = useState('s-1vcpu-1gb')
  const [image, setImage] = useState('ubuntu-24-04-x64')
  const [droplets, setDroplets] = useState<DropletSummary[]>([])
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  async function refresh() {
    try {
      const r = await dropletList()
      setDroplets(r.droplets ?? [])
      setErr('')
    } catch (e) {
      setErr(String(e))
    }
  }

  useEffect(() => { void refresh() }, [])

  async function create() {
    setMsg('')
    setErr('')
    try {
      const r = await dropletCreate({ name, region, size, image })
      setMsg('created droplet ' + (r.droplet?.name ?? '') + ' (id ' + (r.droplet?.id ?? '?') + ')')
      void refresh()
    } catch (e) {
      setErr(String(e))
    }
  }

  return (
    <section>
      <h2>Droplet automation (DigitalOcean)</h2>
      <div className="form">
        <label>name <input value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>region <input value={region} onChange={(e) => setRegion(e.target.value)} /></label>
        <label>size <input value={size} onChange={(e) => setSize(e.target.value)} /></label>
        <label>image <input value={image} onChange={(e) => setImage(e.target.value)} /></label>
        <button onClick={create}>Create droplet</button>
        <button onClick={refresh}>Refresh list</button>
      </div>
      <p className="hint">Requires DO_TOKEN on the macos server (export DO_TOKEN=…).</p>
      {msg !== '' && <p className="ok">{msg}</p>}
      {err !== '' && <pre className="error">{err}</pre>}
      <table>
        <thead>
          <tr><th>id</th><th>name</th><th>status</th><th>region</th><th>size</th><th>ip</th></tr>
        </thead>
        <tbody>
          {droplets.map((d) => (
            <tr key={d.id}>
              <td>{d.id}</td>
              <td>{d.name}</td>
              <td>{d.status}</td>
              <td>{typeof d.region === 'string' ? d.region : (d.region?.slug ?? '')}</td>
              <td>{typeof d.size === 'string' ? d.size : (d.size?.slug ?? '')}</td>
              <td>{d.networks?.v4?.find((n) => n.type === 'public')?.ip_address ?? ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
