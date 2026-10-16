import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const api = vi.hoisted(() => ({ get: vi.fn() }))

vi.mock('@/api', () => ({ default: api }))

import TheContinueReading from '@/components/TheContinueReading.vue'

const PARTWAY = [
  { selector: 'a1', title: 'Alpha', progress: 3, total: 12, last_read_time: '2026-01-02T10:00:00Z', directory: 'd1', thumbnail: '/media/a1.jpg' },
  { selector: 'b2', title: 'Beta', progress: 1, total: 2, last_read_time: '2026-01-03T10:00:00Z', directory: null, thumbnail: '/media/b2.jpg' },
]

function mountPanel(selector = '') {
  return mount(TheContinueReading, {
    props: { selector },
    global: {
      mocks: { $router: { push: vi.fn() } },
      stubs: {
        'router-link': { props: ['to'], template: '<a class="shelf-link" :data-selector="to.params.selector"><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  api.get.mockReset()
})

describe('TheContinueReading', () => {
  it('asks the server for books that are partway through', async () => {
    api.get.mockResolvedValue({ data: PARTWAY })
    const wrapper = mountPanel()
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/read/continue/')
    expect(wrapper.text()).toContain('Alpha')
    expect(wrapper.text()).toContain('Beta')
  })

  it('renders nothing when there is nothing to continue', async () => {
    api.get.mockResolvedValue({ data: [] })
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).not.toContain('Continue reading')
  })

  it('shows the progress as a percentage of the book', async () => {
    api.get.mockResolvedValue({ data: PARTWAY })
    const wrapper = mountPanel()
    await flushPromises()

    const bars = wrapper.findAll('.fill')
    expect(bars).toHaveLength(2)
    expect(bars[0].attributes('style')).toContain('width: 25%')
    expect(bars[1].attributes('style')).toContain('width: 50%')
  })

  it('does not divide by zero for a book with no pages', async () => {
    api.get.mockResolvedValue({ data: [{ ...PARTWAY[0], progress: 0, total: 0 }] })
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.find('.fill').attributes('style')).toContain('width: 0%')
  })

  it('links each card to the reader for that book', async () => {
    api.get.mockResolvedValue({ data: PARTWAY })
    const wrapper = mountPanel()
    await flushPromises()

    const links = wrapper.findAll('.shelf-link')
    expect(links).toHaveLength(2)
    expect(links[0].attributes('data-selector')).toBe('a1')
    expect(links[1].attributes('data-selector')).toBe('b2')
  })

  it('marks an on-deck item as the next issue instead of a progress bar', async () => {
    api.get.mockResolvedValue({ data: [{ ...PARTWAY[0], on_deck: true, progress: 0 }] })
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('On deck')
    expect(wrapper.find('.fill').attributes('style')).toContain('width: 0%')
  })

  it('scopes the request to the folder it was given', async () => {
    api.get.mockResolvedValue({ data: [] })
    mountPanel('d1')
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/read/continue/?directory=d1')
  })
})
