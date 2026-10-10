import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import Library from './pages/Library'
import Settings from './pages/Settings'
import Updates from './pages/Updates'

export default function App() {
  return (
    <BrowserRouter>
      <header className="top">
        <h1>Manga Tracker</h1>
        <nav>
          <NavLink to="/" end>Library</NavLink>
          <NavLink to="/updates">Updates</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Library />} />
          <Route path="/updates" element={<Updates />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
