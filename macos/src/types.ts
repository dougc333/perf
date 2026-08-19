export interface RunInfo {
  run_id: string
  script: string
  status: 'queued' | 'running' | 'done' | 'error'
  output: string
  exit_code: number | null
  results: string[]
  started_at: number
  finished_at: number | null
}

export interface DropletSummary {
  id: number
  name: string
  status: string
  region?: { slug?: string } | string | null
  size?: { slug?: string } | string | null
  networks?: { v4?: { type: string; ip_address: string }[] }
  created_at: string
}

export interface ProfilesResponse {
  dirs: { dir: string; files: string[] }[]
}
