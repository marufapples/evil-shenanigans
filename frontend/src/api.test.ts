import { describe, expect, it } from 'vitest'
import { parseMangaDexId } from './api'

describe('parseMangaDexId', () => {
  const id = '0153e96a-fb57-4665-a988-754b4f3aa744'
  it('accepts urls and bare ids', () => {
    expect(parseMangaDexId(`https://mangadex.org/title/${id}/dungeon-odyssey`)).toBe(id)
    expect(parseMangaDexId(` ${id.toUpperCase()} `)).toBe(id)
  })
  it('rejects junk', () => expect(parseMangaDexId('dungeon odyssey')).toBeNull())
})
