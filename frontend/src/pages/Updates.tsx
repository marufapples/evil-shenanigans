import { useEffect, useState } from 'react'
import { api, type ChapterEvent } from '../api'

export default function Updates() {
  const [events, setEvents] = useState<ChapterEvent[]>([])
  useEffect(() => {
    api.events().then(setEvents).catch(() => setEvents([]))
  }, [])
  if (events.length === 0) return <p className="empty">No new chapters detected yet.</p>
  return (
    <ul className="updates">
      {events.map((e) => (
        <li key={e.id}>
          <a href={e.url ?? '#'} target="_blank" rel="noreferrer">
            {e.manga} — chapter {e.chapter}
          </a>
          <time>{new Date(e.detected_at + 'Z').toLocaleString()}</time>
        </li>
      ))}
    </ul>
  )
}
