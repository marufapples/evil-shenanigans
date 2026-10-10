export const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type ListStatus = 'CURRENT' | 'PLANNING' | 'COMPLETED' | 'DROPPED' | 'PAUSED' | 'REPEATING'

export interface Manga {
  id: number
  anilist_id: number
  title: string
  cover: string | null
  publishing_status: string
  total_chapters: number | null
  latest_known_chapter: number | null
}

export interface Entry {
  id: number
  list_status: ListStatus
  progress: number
  score: number | null
  dirty: boolean
  manga: Manga
}

export interface ChapterEvent {
  id: number
  manga: string
  chapter: number
  url: string | null
  detected_at: string
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

export const api = {
  library: (params: { status?: ListStatus; q?: string; sort?: string }) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => v && qs.set(k, v))
    return req<Entry[]>(`/library?${qs}`)
  },
  patch: (id: number, body: Partial<Pick<Entry, 'progress' | 'list_status' | 'score'>>) =>
    req<Entry>(`/library/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  events: () => req<ChapterEvent[]>('/chapters/events'),
}
