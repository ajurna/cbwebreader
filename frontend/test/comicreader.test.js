import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const api = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn() }))
const router = vi.hoisted(() => ({ push: vi.fn() }))
const deck = vi.hoisted(() => ({
  initialize: vi.fn(() => Promise.resolve()),
  slide: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  destroy: vi.fn(),
  isFirstSlide: vi.fn(() => false),
  isLastSlide: vi.fn(() => false),
}))
const hammertime = vi.hoisted(() => ({ on: vi.fn(), off: vi.fn() }))
const reveal = vi.hoisted(() => vi.fn(() => deck))

vi.mock('@/api', () => ({ default: api }))
vi.mock('reveal.js', () => ({ default: reveal }))
vi.mock('hammerjs', () => ({ default: vi.fn(function () { return hammertime }) }))

import TheComicReader from '@/components/TheComicReader.vue'

const COMIC = {
  title: 'Alpha',
  last_read_page: 2,
  pages: 5,
  prev_comic: { route: 'browse', selector: 'p1' },
  next_comic: { route: 'browse', selector: 'n1' },
}

const mounted = []

function mountReader() {
  const wrapper = mount(TheComicReader, {
    props: { selector: 'a1' },
    global: {
      mocks: { $router: router },
      stubs: { 'comic-paginate': true },
    },
  })
  mounted.push(wrapper)
  return wrapper
}

beforeEach(() => {
  vi.useFakeTimers()
  HTMLElement.prototype.scrollIntoView = vi.fn()
  api.get.mockReset()
  api.put.mockReset()
  api.get.mockResolvedValue({ data: { ...COMIC } })
  api.put.mockResolvedValue({ data: {} })
  router.push.mockReset()
  reveal.mockClear()
  for (const fn of Object.values(deck)) {
    if (typeof fn === 'function') fn.mockClear?.()
  }
  for (const fn of Object.values(hammertime)) fn.mockClear()
})

afterEach(() => {
  mounted.forEach((wrapper) => {
    if (!wrapper.vm?.isUnmounted) wrapper.unmount()
  })
  mounted.length = 0
})

describe('TheComicReader', () => {
  it('loads the book, starts the deck and records the page it resumed on', async () => {
    const wrapper = mountReader()
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/api/read/a1/')
    expect(deck.initialize).toHaveBeenCalled()
    expect(wrapper.vm.current_page).toBe(2)
    expect(deck.slide).toHaveBeenCalledWith(2)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 2 })
  })

  it('keeps the page indicator in step with the deck', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.setPage(4)
    expect(deck.slide).toHaveBeenCalledWith(3)
    await flushPromises()
    expect(wrapper.vm.paginate_page).toBe(4)
  })

  it('debounces arrow keys so held keys do not spam the deck', async () => {
    const wrapper = mountReader()
    await flushPromises()

    window.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowRight' }))
    window.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowRight' }))
    vi.advanceTimersByTime(50)

    expect(deck.slide).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.current_page).toBe(3)
  })

  it('moves to the next book when the last slide is reached', async () => {
    const wrapper = mountReader()
    await flushPromises()

    deck.isLastSlide.mockReturnValueOnce(true)
    wrapper.vm.keyPress({ key: 'ArrowRight' })

    expect(router.push).toHaveBeenCalledWith({ name: 'browse', params: { selector: 'n1' } })
  })

  it('moves to the previous book when the first slide is reached', async () => {
    const wrapper = mountReader()
    await flushPromises()

    deck.isFirstSlide.mockReturnValueOnce(true)
    wrapper.vm.keyPress({ key: 'ArrowLeft' })

    expect(router.push).toHaveBeenCalledWith({ name: 'browse', params: { selector: 'p1' } })
  })

  it('records the page again whenever the visible slide changes', async () => {
    mountReader()
    await flushPromises()

    const handler = deck.on.mock.calls[0][1]
    api.put.mockClear()

    handler({ indexh: 4 })

    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 4 })
  })

  it('removes every listener and the deck when it is unmounted', async () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    const removeSpy = vi.spyOn(window, 'removeEventListener')

    const wrapper = mountReader()
    await flushPromises()

    expect(addSpy).toHaveBeenCalledWith('keyup', wrapper.vm.keyPressDebounce)

    wrapper.unmount()

    expect(removeSpy).toHaveBeenCalledWith('keyup', wrapper.vm.keyPressDebounce)
    expect(deck.off).toHaveBeenCalledWith('slidechanged', wrapper.vm.slideChanged)
    expect(deck.destroy).toHaveBeenCalled()
    expect(hammertime.off).toHaveBeenCalledWith('swipeleft')
    expect(hammertime.off).toHaveBeenCalledWith('swiperight')
    expect(hammertime.off).toHaveBeenCalledWith('tap')

    addSpy.mockRestore()
    removeSpy.mockRestore()
  })

  it('does not act on a key press that was debounced just before unmounting', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    window.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowRight' }))
    wrapper.unmount()
    vi.advanceTimersByTime(100)

    expect(deck.slide).not.toHaveBeenCalled()
  })
})
