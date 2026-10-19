import { describe, expect, it } from 'vitest'

import ComicCard from '@/components/ComicCard.vue'

// The card itself needs a router, a store and a toast plugin, so test the metadata line
// by calling the computed with a stand-in component instance.
const details = (data) => ComicCard.computed.details.call({ data })

describe('ComicCard metadata line', () => {
  it('lists the metadata that is present', () => {
    expect(details({
      metadata: {
        series: 'Test Series',
        issue: '12',
        writer: 'Test Writer',
        artist: 'Test Artist',
        year: 2003,
      },
    })).toBe('Test Series #12 · Test Writer · Test Artist · 2003')
  })

  it('leaves out the parts that are missing', () => {
    expect(details({ metadata: { series: '', issue: '12', writer: '', artist: '', year: null } }))
      .toBe('#12')
    expect(details({ metadata: { series: 'Test Series', issue: '', writer: '', artist: '', year: null } }))
      .toBe('Test Series')
    expect(details({ metadata: { series: '', issue: '', writer: 'Test Writer', artist: '', year: null } }))
      .toBe('Test Writer')
  })

  it('returns nothing for a folder or a book with no metadata', () => {
    expect(details({ type: 'Directory', metadata: {} })).toBe('')
    expect(details({ type: 'ComicBook', metadata: undefined })).toBe('')
  })
})
