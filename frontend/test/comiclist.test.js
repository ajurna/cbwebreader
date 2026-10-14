import { beforeEach, describe, expect, it, vi } from 'vitest'
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

function mountList(props = {}) {
  return mount(TheComicList, {
    props: { selector: props.selector ?? '' },
    global: {
      stubs: {
        'font-awesome-icon': true,
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
  api.get.mockResolvedValue({ data: [...BOOKS] })
  store.state.filters = {}
})

describe('TheComicList', () => {
  it('loads the home listing when it is mounted', async () => {
    const wrapper = mountList()
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/browse/')
    expect(wrapper.text()).toContain('Alpha')
  })

  it('loads the listing for the folder it was given', async () => {
    const wrapper = mountList({ selector: 'c3' })
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/browse/c3/')
    expect(wrapper.vm.comics).toHaveLength(3)
  })

  it('filters by name without changing the loaded data', async () => {
    const wrapper = mountList()
    await flushPromises()

    wrapper.vm.filters.search_string = 'beta'
    expect(wrapper.vm.filteredComics.map((c) => c.title)).toEqual(['Beta'])

    wrapper.vm.filters.search_string = 'ga'
    expect(wrapper.vm.filteredComics.map((c) => c.title)).toEqual(['Gamma Subfolder'])
  })

  it('filters read and unread entries separately', async () => {
    const wrapper = mountList()
    await flushPromises()

    wrapper.vm.filters.filter_read = true
    expect(wrapper.vm.filteredComics.map((c) => c.title)).toEqual(['Alpha'])

    wrapper.vm.filters.filter_read = false
    wrapper.vm.filters.filter_unread = true
    expect(wrapper.vm.filteredComics.map((c) => c.title)).toEqual(['Beta'])
  })

  it('keeps the filters in the store so they survive a folder change', async () => {
    const wrapper = mountList({ selector: 'c3' })
    await flushPromises()

    wrapper.vm.filters.search_string = 'alpha'
    expect(store.state.filters.c3.search_string).toBe('alpha')
  })

  it('scans the folder on disk and uses the returned listing', async () => {
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

    resolvePost({ data: [{ selector: 'd4', title: 'Delta', type: 'ComicBook' }] })
    await flushPromises()

    expect(wrapper.vm.comics).toHaveLength(1)
    expect(wrapper.vm.scanning).toBe(false)
  })

  it('marks every book in the folder, ignoring subfolders', async () => {
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
