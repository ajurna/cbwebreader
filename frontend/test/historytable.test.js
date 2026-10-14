import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const api = vi.hoisted(() => ({ get: vi.fn() }))

vi.mock('@/api', () => ({ default: api }))

import HistoryTable from '@/components/HistoryTable.vue'

function mountTable() {
  return mount(HistoryTable, { global: { stubs: { paginate: true, 'font-awesome-icon': true } } })
}

beforeEach(() => {
  vi.useFakeTimers()
  api.get.mockReset()
  api.get.mockResolvedValue({ data: { count: 25, results: [{ id: 1, selector: 'a1', file_name: 'Alpha', last_read_time: new Date(), unread: false, finished: true, last_read_page: 3, page_count: 5 }] } })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('HistoryTable', () => {
  it('requests the first page when it is mounted', async () => {
    const wrapper = mountTable()
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/history/', { params: { page: 1, page_size: 10 } })
    expect(wrapper.text()).toContain('Finished')
  })

  it('works out how many pages the result count implies', async () => {
    const wrapper = mountTable()
    await flushPromises()

    expect(wrapper.vm.page_count).toBe(3)

    wrapper.vm.page_size = 25
    wrapper.vm.setPage(2)
    await flushPromises()

    expect(api.get).toHaveBeenLastCalledWith('/api/history/', { params: { page: 2, page_size: 25 } })
    expect(wrapper.vm.page_count).toBe(1)
  })

  it('includes the search text once there is one', async () => {
    const wrapper = mountTable()
    await flushPromises()

    wrapper.vm.search_text = 'alpha'
    wrapper.vm.setPage(1)
    await flushPromises()

    expect(api.get).toHaveBeenLastCalledWith('/api/history/', {
      params: { page: 1, page_size: 10, search_text: 'alpha' },
    })
  })

  it('debounces typing so one burst of keystrokes makes one request', async () => {
    const wrapper = mountTable()
    await flushPromises()
    expect(api.get).toHaveBeenCalledTimes(1)

    wrapper.vm.debounceInput()
    wrapper.vm.debounceInput()
    wrapper.vm.debounceInput()

    vi.advanceTimersByTime(500)
    await flushPromises()

    expect(api.get).toHaveBeenCalledTimes(2)
  })

  it('does not fire a pending debounce after the table is removed', async () => {
    const wrapper = mountTable()
    await flushPromises()

    wrapper.vm.debounceInput()
    wrapper.unmount()

    vi.advanceTimersByTime(1000)
    await flushPromises()

    expect(api.get).toHaveBeenCalledTimes(1)
  })

  it('goes back to page one when the page number is no longer valid', async () => {
    api.get.mockRejectedValueOnce({ response: { data: { detail: 'Invalid page.' } } })

    const wrapper = mountTable()
    await flushPromises()

    expect(wrapper.vm.page).toBe(1)
    expect(api.get).toHaveBeenCalledTimes(2)
  })

  it('shows the reading status for each entry', async () => {
    const wrapper = mountTable()
    await flushPromises()

    expect(wrapper.vm.get_status({ unread: true })).toBe('Unread')
    expect(wrapper.vm.get_status({ unread: null })).toBe('Unread')
    expect(wrapper.vm.get_status({ unread: false, finished: true })).toBe('Finished')
    expect(wrapper.vm.get_status({ unread: false, finished: false, last_read_page: 2, page_count: 5 })).toBe('2 / 5')
  })
})
