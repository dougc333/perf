import type { DropletSummary, ProfilesResponse, RunInfo } from './types'

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'content-type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(await res.text())
  return (await res.json()) as T
}

export const health = () => api<{ ok: boolean; dropletApi: string; hasDoToken: boolean }>('/api/health')

export const dropletRun = (script: string) =>
  api<{ run_id: string }>('/api/droplet/run', { method: 'POST', body: JSON.stringify({ script }) })

export const dropletRunStatus = (id: string) => api<RunInfo>('/api/droplet/run/' + id)

export const dropletList = () => api<{ droplets: DropletSummary[] }>('/api/droplet/list')

export const dropletCreate = (p: { name: string; region: string; size: string; image: string }) =>
  api<{ droplet: DropletSummary }>('/api/droplet/create', { method: 'POST', body: JSON.stringify(p) })

export const runPostprocess = (runDir?: string) =>
  api<{ ok: boolean; code: number; output: string }>('/api/postprocess', {
    method: 'POST',
    body: JSON.stringify({ runDir }),
  })

export const listProfiles = () => api<ProfilesResponse>('/api/profiles')
