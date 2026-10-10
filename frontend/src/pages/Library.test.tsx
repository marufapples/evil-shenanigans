import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Entry } from '../api'
import { Card, unread } from './Library'

const entry = (over: Partial<Entry['manga']> = {}, progress = 5): Entry => ({
  id: 1, list_status: 'CURRENT', progress, score: null, dirty: false,
  manga: { id: 1, anilist_id: 1, title: 'Berserk', cover: null, publishing_status: 'RELEASING', total_chapters: null, latest_known_chapter: 8, ...over },
})

describe('unread', () => {
  it('counts chapters ahead of progress', () => expect(unread(entry())).toBe(3))
  it('is zero when unknown or caught up', () => {
    expect(unread(entry({ latest_known_chapter: null }))).toBe(0)
    expect(unread(entry({ latest_known_chapter: 4 }))).toBe(0)
  })
})

describe('Card', () => {
  it('shows badge and bumps progress', () => {
    const onBump = vi.fn()
    render(<Card entry={entry()} onBump={onBump} />)
    expect(screen.getByText('3 new')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Berserk/ }))
    expect(onBump).toHaveBeenCalledOnce()
  })
})
