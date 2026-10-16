import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), put: vi.fn() }))
const store = vi.hoisted(() => ({ state: { filters: {} }, getters: { isAuthenticated: true, is_superuser: false } }))

vi.mock('@/api', () => ({ default: api }))
vi.mock('@/store', () => ({ default: store }))

import TheComicList from '@/components/TheComicList.vue'

const BOOKS = [
  { selector: 'a1', title: 'Alpha', type: 'ComicBook', finished: true, unread: false, thumbnail: '' },
  { selector: 'b2', title: 'Beta', type: 'ComicBook', finished: false, unread: true, thumbnail: '' },
  { selector: 'c3', title: 'Gamma Subfolder', type: 'Directory', thumbnail: '' },
]

function page(results, count = results.length, page_size = 10) {
  return { data: { count, page_size, results } }
}

function mountList(props = {}) {
  return mount(TheComicList, {
    props: { selector: props.selector ?? '' },
    global: {
      stubs: {
        'font-awesome-icon': true,
        paginate: {
          name: 'Paginate',
          props: ['pageCount'],
          template: '<div class="pager-stub">{{ pageCount }}</div>',
        },
        ComicCard: {
          name: 'ComicCard',
          props: ['data'],
          template: '<div class="card-stub" :data-selector="data.title">{{ data.title }}</div>',
        },
      },
    },
  })
}

beforeEach(() => {
  api.get.mockReset()
  api.post.mockReset()
  api.put.mockReset()
  api.get.mockResolvedValue(page(BOOKS))
  store.state.filters = {}
})

afterEach(() => {
  vi.useRealTimers()
})

describe('TheComicList', () => {
  it('loads the first page of the home listing when it is mounted', async () => {
    const wrapper = mountList()
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/browse/', { params: { page: 1, page_size: 10 } })
    expect(wrapper.text()).toContain('Alpha')
  })

  it('loads the listing for the folder it was given', async () => {
    const wrapper = mountList({ selector: 'c3' })
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/browse/c3/', { params: { page: 1, page_size: 10 } })
    expect(wrapper.vm.comics).toHaveLength(3)
  })

  it('shows the pager only when there is more than one page', async () => {
    api.get.mockResolvedValue(page(BOOKS, 12))
    const wrapper = mountList()
    await flushPromises()

    expect(wrapper.vm.page_count).toBe(2)
    expect(wrapper.text()).toContain('Showing page 1 of 2')
    expect(wrapper.find('.pager-stub').text()).toBe('2')
  })

  it('keeps the search box when there is only one page', async () => {
    const wrapper = mountList()
    await flushPromises()

    expect(wrapper.vm.page_count).toBe(1)
    expect(wrapper.find('.pager-stub').exists()).toBe(false)
    expect(wrapper.find('input[aria-label="Filter comics by name"]').exists()).toBe(true)
  })

  it('searches on the server after the debounce', async () => {
    const wrapper = mountList()
    await flushPromises()

    vi.useFakeTimers()
    wrapper.find('input[aria-label="Filter comics by name"]').setValue('beta')
    vi.advanceTimersByTime(500)

    expect(api.get).toHaveBeenLastCalledWith('/api/browse/', { params: { page: 1, page_size: 10, search: 'beta' } })
  })

  it('sends the read filter as a query parameter', async () => {
    const wrapper = mountList()
    await flushPromises()

    vi.useFakeTimers()
    wrapper.vm.setFilter('read')
    vi.advanceTimersByTime(500)

    expect(api.get).toHaveBeenLastCalledWith('/api/browse/', { params: { page: 1, page_size: 10, read: 'true' } })
  })

  it('requests another page when the pager is used', async () => {
    api.get.mockResolvedValue(page(BOOKS, 12))
    const wrapper = mountList()
    await flushPromises()

    wrapper.vm.setPage(2)
    await flushPromises()

    expect(api.get).toHaveBeenLastCalledWith('/api/browse/', { params: { page: 2, page_size: 10 } })
  })

  it('goes back to the first page when the page number is no longer valid', async () => {
    const wrapper = mountList()
    await flushPromises()

    api.get.mockRejectedValueOnce({ response: { data: { detail: 'Invalid page.' } } })
    wrapper.vm.setPage(3)
    await flushPromises()

    expect(wrapper.vm.page).toBe(1)
    expect(api.get).toHaveBeenLastCalledWith('/api/browse/', { params: { page: 1, page_size: 10 } })
  })

  it('restores the filters saved for that folder', async () => {
    store.state.filters.c3 = { search_string: 'alpha', filter_read: true, filter_unread: false }
    const wrapper = mountList({ selector: 'c3' })
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/browse/c3/', {
      params: { page: 1, page_size: 10, search: 'alpha', read: 'true' },
    })
    expect(wrapper.vm.filters.filter_read).toBe(true)
  })

  it('keeps the filters in the store so they survive a folder change', async () => {
    const wrapper = mountList({ selector: 'c3' })
    await flushPromises()

    wrapper.vm.filters.search_string = 'alpha'
    expect(store.state.filters.c3.search_string).toBe('alpha')
  })

  it('scans the folder on disk and uses the returned page', async () => {
    let resolvePost
    api.post.mockImplementation(() => new Promise((resolve) => { resolvePost = resolve }))

    const wrapper = mountList({ selector: 'c3' })
    await flushPromises()

    const button = wrapper.find('button[title="Read this folder from disk again"]')
    button.trigger('click')
    await wrapper.vm.$nextTick()

    expect(api.post).toHaveBeenCalledWith('/api/browse/scan/', { selector: 'c3' })
    expect(wrapper.vm.scanning).toBe(true)
    expect(button.element.disabled).toBe(true)

    resolvePost(page([{ selector: 'd4', title: 'Delta', type: 'ComicBook' }]))
    await flushPromises()

    expect(wrapper.vm.comics).toHaveLength(1)
    expect(wrapper.vm.scanning).toBe(false)
  })

  it('marks only the books on the page it is showing', async () => {
    const wrapper = mountList()
    await flushPromises()

    api.put.mockResolvedValue({ data: [] })
    wrapper.vm.markAll('mark_read')
    await flushPromises()

    expect(api.put).toHaveBeenCalledWith('/api/action/mark_read/', { selectors: ['a1', 'b2'] })
  })

  it('marks everything before the card that asked for it', async () => {
    const wrapper = mountList()
    await flushPromises()

    api.put.mockResolvedValue({ data: [] })
    wrapper.vm.markPreviousRead('b2')
    await flushPromises()

    expect(api.put).toHaveBeenCalledWith('/api/action/mark_read/', { selectors: ['a1', 'b2'] })
  })
})
