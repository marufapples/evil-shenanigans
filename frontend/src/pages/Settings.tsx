import { useCallback, useEffect, useState } from 'react'
import { API, api, parseMangaDexId, type Match } from '../api'

function Action({ label, run }: { label: string; run: () => Promise<unknown> }) {
  const [out, setOut] = useState<string>('')
  const [busy, setBusy] = useState(false)
  return (
    <div className="action">
      <button
        disabled={busy}
        onClick={async () => {
          setBusy(true)
          try {
            setOut(JSON.stringify(await run()))
          } catch (e) {
            setOut(`Failed: ${(e as Error).message}`)
          } finally {
            setBusy(false)
          }
        }}
      >
        {busy ? 'Working…' : label}
      </button>
      {out && <code>{out}</code>}
    </div>
  )
}

function MatchRow({ m, onSaved }: { m: Match; onSaved: () => void }) {
  const [value, setValue] = useState('')
  const id = parseMangaDexId(value)
  return (
    <tr>
      <td>{m.title}</td>
      <td>
        {m.mangadex_id ? (
          <a href={`https://mangadex.org/title/${m.mangadex_id}`} target="_blank" rel="noreferrer">linked</a>
        ) : (
          <span className="muted">not found</span>
        )}
        {m.latest_known_chapter != null && <span className="muted"> · ch {m.latest_known_chapter}</span>}
      </td>
      <td>
        <input placeholder="MangaDex URL or id" value={value} onChange={(e) => setValue(e.target.value)} />
        <button disabled={!id} onClick={() => api.setMatch(m.id, id).then(() => { setValue(''); onSaved() })}>
          Save
        </button>
      </td>
    </tr>
  )
}

export default function Settings() {
  const [auth, setAuth] = useState<{ connected: boolean; account: string | null } | null>(null)
  const [jobs, setJobs] = useState<Awaited<ReturnType<typeof api.jobs>>>({})
  const [matches, setMatches] = useState<Match[]>([])

  const load = useCallback(() => {
    api.authStatus().then(setAuth).catch(() => setAuth(null))
    api.jobs().then(setJobs).catch(() => setJobs({}))
    api.matches().then(setMatches).catch(() => setMatches([]))
  }, [])
  useEffect(load, [load])

  return (
    <div className="settings">
      <section>
        <h2>AniList</h2>
        {auth?.connected ? (
          <p>
            Connected as <strong>{auth.account}</strong>. Progress changes sync back to AniList.{' '}
            <button onClick={() => api.logout().then(load)}>Disconnect</button>
          </p>
        ) : (
          <p>
            Not connected; changes stay local until you connect.{' '}
            <a className="button" href={`${API}/auth/anilist/login`}>Connect AniList</a>
          </p>
        )}
        <Action label="Import from AniList now" run={api.importNow} />
        <Action label="Push pending changes" run={api.pushNow} />
      </section>

      <section>
        <h2>Notifications</h2>
        <Action label="Check for new chapters now" run={api.checkChapters} />
        <Action label="Send test Discord message" run={api.testNotify} />
      </section>

      <section>
        <h2>Reading-site sync</h2>
        <p>
          Install <a href={`${API}/progress/userscript`} target="_blank" rel="noreferrer">the userscript</a> in
          Tampermonkey. When you open a chapter page on any site, your progress moves forward automatically.
        </p>
      </section>

      <section>
        <h2>Background jobs</h2>
        {Object.keys(jobs).length === 0 ? (
          <p className="muted">No runs yet (jobs run every 10–30 minutes while the backend is up).</p>
        ) : (
          <ul>
            {Object.entries(jobs).map(([name, j]) => (
              <li key={name}>
                <strong>{name}</strong> {j.ok ? 'ok' : 'failed'} · {new Date(j.last_run + 'Z').toLocaleString()} ·{' '}
                <code>{j.message}</code>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Chapter sources</h2>
        <p className="muted">Series you're reading and their MangaDex match. Paste a MangaDex link to fix or add one.</p>
        <table className="matches">
          <tbody>
            {matches.map((m) => (
              <MatchRow key={m.id} m={m} onSaved={load} />
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
