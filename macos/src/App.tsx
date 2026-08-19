import { useState } from 'react'
import DropletPanel from './components/DropletPanel'
import RunPanel from './components/RunPanel'
import PostProcessPanel from './components/PostProcessPanel'
import ResultsPanel from './components/ResultsPanel'
import './styles.css'

type Tab = 'run' | 'droplet' | 'postprocess' | 'results'

const TABS: { id: Tab; label: string }[] = [
  { id: 'run', label: 'Run on droplet' },
  { id: 'droplet', label: 'Droplet' },
  { id: 'postprocess', label: 'Post-process' },
  { id: 'results', label: 'Results' },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('run')
  return (
    <div className="app">
      <header>
        <h1>perf dashboard</h1>
        <p className="subtitle">droplet automation · script runs · post-processing</p>
      </header>
      <nav>
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <main>
        {tab === 'run' && <RunPanel />}
        {tab === 'droplet' && <DropletPanel />}
        {tab === 'postprocess' && <PostProcessPanel />}
        {tab === 'results' && <ResultsPanel />}
      </main>
    </div>
  )
}
