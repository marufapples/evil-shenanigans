import { useCallback, useEffect, useState } from 'react'
import { api, type Entry, type ListStatus } from '../api'

const TABS: { label: string; value?: ListStatus }[] = [
  { label: 'All' },
  { label: 'Reading', value: 'CURRENT' },
  { label: 'Planning', value: 'PLANNING' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Paused', value: 'PAUSED' },
  { label: 'Dropped', value: 'DROPPED' },
]

export function unread(e: Entry): number {
  const latest = e.manga.latest_known_chapter
  return latest == null ? 0 : Math.max(0, Math.floor(latest) - e.progress)
}

export function Card({ entry, onBump }: { entry: Entry; onBump: (e: Entry) => void }) {
  const behind = unread(entry)
  const total = entry.manga.total_chapters
  return (
    <article className="card">
      {entry.manga.cover && <img src={entry.manga.cover} alt="" loading="lazy" />}
      {behind > 0 && <span className="badge">{behind} new</span>}
      <div className="meta">
        <h3>{entry.manga.title}</h3>
        <p>
          Ch. {entry.progress}
          {total ? ` / ${total}` : ''}
          {entry.dirty && <span title="Not yet synced to AniList"> •</span>}
        </p>
        <button onClick={() => onBump(entry)} aria-label={`Mark next chapter of ${entry.manga.title} read`}>
          +1
        </button>
      </div>
    </article>
  )
}

export default function Library() {
  const [status, setStatus] = useState<ListStatus | undefined>('CURRENT')
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('updated')
  const [entries, setEntries] = useState<Entry[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    api.library({ status, q, sort }).then(setEntries).catch((e) => setError(String(e.message)))
  }, [status, q, sort])
  useEffect(load, [load])

  const bump = async (e: Entry) => {
    setEntries((es) => es.map((x) => (x.id === e.id ? { ...x, progress: x.progress + 1 } : x)))
    try {
      const updated = await api.patch(e.id, { progress: e.progress + 1 })
      setEntries((es) => es.map((x) => (x.id === e.id ? updated : x)))
    } catch {
      load()
    }
  }

  return (
    <>
      <div className="toolbar">
        <div className="tabs" role="tablist">
          {TABS.map((t) => (
            <button key={t.label} role="tab" aria-selected={status === t.value} onClick={() => setStatus(t.value)}>
              {t.label}
            </button>
          ))}
        </div>
        <input placeholder="Search titles" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
          <option value="updated">Recently updated</option>
          <option value="title">Title</option>
          <option value="progress">Progress</option>
          <option value="score">Score</option>
        </select>
      </div>
      {error && <p className="error">The tracker server isn’t running ({error}). Start everything with ./run.sh in the project folder.</p>}
      {!error && entries.length === 0 && <p className="empty">Nothing here yet.</p>}
      <div className="grid">
        {entries.map((e) => (
          <Card key={e.id} entry={e} onBump={bump} />
        ))}
      </div>
    </>
  )
}
