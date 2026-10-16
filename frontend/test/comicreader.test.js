import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'

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
const store = vi.hoisted(() => ({
  state: { reader_mode: 'paged' },
  commit: vi.fn(),
}))

const observers = []

// jsdom has no IntersectionObserver, so the tests drive the callbacks by hand.
class FakeIntersectionObserver {
  constructor(callback, options) {
    this.callback = callback
    this.options = options
    this.targets = []
    this.disconnected = false
    observers.push(this)
  }

  observe(target) {
    if (!this.targets.includes(target)) this.targets.push(target)
  }

  unobserve(target) { this.targets = this.targets.filter((item) => item !== target) }
  disconnect() { this.disconnected = true; this.targets = [] }
  fire(entries) { this.callback(entries, this) }
}

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
      mocks: { $router: router, $store: store },
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
  store.state = reactive({ reader_mode: 'paged' })
  store.commit.mockReset()
  store.commit.mockImplementation((name, value) => {
    if (name === 'setReaderMode' && (value === 'paged' || value === 'scroll')) {
      store.state.reader_mode = value
    }
  })
  observers.length = 0
  globalThis.IntersectionObserver = FakeIntersectionObserver
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

  it('acts on the first arrow key and ignores held keys until the throttle expires', async () => {
    const wrapper = mountReader()
    await flushPromises()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))
    expect(wrapper.vm.current_page).toBe(3)
    expect(deck.slide).toHaveBeenCalledTimes(2)

    vi.advanceTimersByTime(100)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))
    expect(wrapper.vm.current_page).toBe(4)
    expect(deck.slide).toHaveBeenCalledTimes(3)
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

    expect(addSpy).toHaveBeenCalledWith('keydown', wrapper.vm.keyPress)

    wrapper.unmount()

    expect(removeSpy).toHaveBeenCalledWith('keydown', wrapper.vm.keyPress)
    expect(deck.off).toHaveBeenCalledWith('slidechanged', wrapper.vm.slideChanged)
    expect(deck.destroy).toHaveBeenCalled()
    expect(hammertime.off).toHaveBeenCalledWith('swipeleft')
    expect(hammertime.off).toHaveBeenCalledWith('swiperight')
    expect(hammertime.off).toHaveBeenCalledWith('tap')

    addSpy.mockRestore()
    removeSpy.mockRestore()
  })

  it('leaves arrow keys with a modifier to the browser', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    wrapper.vm.keyPress({ key: 'ArrowLeft', altKey: true })
    expect(deck.slide).not.toHaveBeenCalled()

    wrapper.vm.keyPress({ key: 'ArrowRight' })
    expect(wrapper.vm.current_page).toBe(3)
  })

  it('ignores arrow keys pressed while a form control has focus', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    wrapper.vm.keyPress({ key: 'ArrowRight', target: document.createElement('input') })
    expect(deck.slide).not.toHaveBeenCalled()

    wrapper.vm.keyPress({ key: 'ArrowRight', target: document.createElement('button') })
    expect(deck.slide).not.toHaveBeenCalled()
  })

  it('leaves Up and Down to the browser so they scroll within the page', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()
    api.put.mockClear()

    wrapper.vm.keyPress({ key: 'ArrowDown' })
    wrapper.vm.keyPress({ key: 'ArrowUp' })

    // Nothing is intercepted, so the native scroll is not doubled up and the recorded
    // page stays where the reader actually is.
    expect(wrapper.vm.current_page).toBe(2)
    expect(deck.slide).not.toHaveBeenCalled()
    expect(api.put).not.toHaveBeenCalled()
  })

  it('shows the shortcut list with ? and hides it again', async () => {
    const wrapper = mountReader()
    await flushPromises()

    expect(wrapper.find('.shortcuts').exists()).toBe(false)

    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    expect(wrapper.find('.shortcuts').exists()).toBe(true)

    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    expect(wrapper.find('.shortcuts').exists()).toBe(false)
  })

  it('hides the shortcut list with Escape even when a control has focus', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    expect(wrapper.find('.shortcuts').exists()).toBe(true)

    wrapper.vm.keyPress({ key: 'Escape', target: document.createElement('input') })
    await flushPromises()
    expect(wrapper.find('.shortcuts').exists()).toBe(false)
  })

  it('toggles the shortcut list from the ? button', async () => {
    const wrapper = mountReader()
    await flushPromises()

    const button = wrapper.find('button[aria-pressed]')
    await button.trigger('click')
    expect(wrapper.find('.shortcuts').exists()).toBe(true)
    expect(button.attributes('aria-pressed')).toBe('true')
  })

  it('pages with Space and Shift+Space', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    const preventDefault = vi.fn()
    wrapper.vm.keyPress({ key: ' ', preventDefault })
    expect(preventDefault).toHaveBeenCalled()
    expect(deck.slide).toHaveBeenCalledWith(3)

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: ' ', shiftKey: true, preventDefault })
    expect(deck.slide).toHaveBeenCalledWith(2)
  })

  it('pages with n and p whatever the case', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    wrapper.vm.keyPress({ key: 'n' })
    expect(deck.slide).toHaveBeenCalledWith(3)

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: 'P' })
    expect(deck.slide).toHaveBeenCalledWith(2)
  })

  it('jumps to the first and last page with Home and End', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    const preventDefault = vi.fn()
    wrapper.vm.keyPress({ key: 'Home', preventDefault })
    expect(preventDefault).toHaveBeenCalled()
    expect(deck.slide).toHaveBeenCalledWith(0)

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: 'End', preventDefault })
    expect(deck.slide).toHaveBeenCalledWith(4)
  })

  it('switches reading mode with m', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.keyPress({ key: 'm' })
    await flushPromises()

    expect(store.commit).toHaveBeenCalledWith('setReaderMode', 'scroll')
    expect(wrapper.vm.mode).toBe('scroll')
  })

  it('shows the top of the page when changing pages in paged mode', async () => {
    const wrapper = mountReader()
    await flushPromises()
    const scrollIntoView = HTMLElement.prototype.scrollIntoView

    wrapper.vm.keyPress({ key: 'ArrowRight' })
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'auto', block: 'start' })
  })

  it('does not move the deck when a key arrives before reveal has initialized', async () => {
    const wrapper = mountReader()
    deck.slide.mockClear()

    wrapper.vm.keyPress({ key: 'ArrowRight' })
    expect(deck.slide).not.toHaveBeenCalled()

    await flushPromises()
    expect(deck.initialize).toHaveBeenCalled()

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: 'ArrowRight' })
    expect(wrapper.vm.current_page).toBe(3)
    expect(deck.slide).toHaveBeenCalledWith(3)
  })
})

describe('TheComicReader in continuous mode', () => {
  function mountContinuous(pageCount) {
    store.state.reader_mode = 'scroll'
    api.get.mockResolvedValue({ data: { ...COMIC, pages: pageCount } })
    return mountReader()
  }

  function growthObserver() {
    return observers.find((observer) => observer.options.rootMargin)
  }

  function pageObserver() {
    return observers.find((observer) => !observer.options.rootMargin)
  }

  it('renders only the first window of pages and does not start a deck', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    expect(wrapper.vm.rendered).toBe(20)
    expect(wrapper.findAll('section[data-page]')).toHaveLength(20)
    expect(reveal).not.toHaveBeenCalled()
  })

  it('renders far enough to include the page it resumed on', async () => {
    store.state.reader_mode = 'scroll'
    api.get.mockResolvedValue({ data: { ...COMIC, last_read_page: 30, pages: 45 } })
    const wrapper = mountReader()
    await flushPromises()

    expect(wrapper.vm.rendered).toBe(31)
    expect(wrapper.findAll('section[data-page]')).toHaveLength(31)
  })

  it('grows the window when the reader reaches the end of what is rendered', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    growthObserver().fire([{ isIntersecting: true, target: wrapper.find('.sentinel').element, boundingClientRect: { top: 0 } }])
    await flushPromises()

    expect(wrapper.vm.rendered).toBe(40)
    expect(wrapper.findAll('section[data-page]')).toHaveLength(40)
    expect(pageObserver().targets).toHaveLength(40)
  })

  it('does not grow past the last page', async () => {
    const wrapper = mountContinuous(25)
    await flushPromises()

    growthObserver().fire([{ isIntersecting: true, target: wrapper.find('.sentinel').element, boundingClientRect: { top: 0 } }])
    await flushPromises()

    expect(wrapper.vm.rendered).toBe(25)
    expect(wrapper.find('.sentinel').exists()).toBe(false)
  })

  it('records the page at the top of the viewport', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    pageObserver().fire([
      { isIntersecting: true, target: sections[4].element, boundingClientRect: { top: 10 } },
      { isIntersecting: true, target: sections[2].element, boundingClientRect: { top: 400 } },
    ])

    expect(wrapper.vm.current_page).toBe(4)
    vi.advanceTimersByTime(500)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 4 })
  })

  it('keeps the recorded page while scrolling inside a page taller than the viewport', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    const observer = pageObserver()
    observer.fire([{ isIntersecting: true, target: sections[4].element, boundingClientRect: { top: 0 } }])
    vi.advanceTimersByTime(500)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 4 })

    // Scrolling down inside that page leaves it topmost, so nothing is written.
    api.put.mockClear()
    observer.fire([{ isIntersecting: true, target: sections[4].element, boundingClientRect: { top: -300 } }])
    vi.advanceTimersByTime(500)
    expect(wrapper.vm.current_page).toBe(4)
    expect(api.put).not.toHaveBeenCalled()

    // The recorded page only changes when the next page becomes the topmost one.
    observer.fire([
      { isIntersecting: false, target: sections[4].element },
      { isIntersecting: true, target: sections[5].element, boundingClientRect: { top: 0 } },
    ])
    vi.advanceTimersByTime(500)
    expect(wrapper.vm.current_page).toBe(5)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 5 })
  })

  it('writes once for a burst of scrolling rather than once per intersection', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    const observer = pageObserver()
    observer.fire([{ isIntersecting: true, target: sections[5].element, boundingClientRect: { top: 400 } }])
    observer.fire([{ isIntersecting: true, target: sections[6].element, boundingClientRect: { top: 0 } }])
    vi.advanceTimersByTime(500)

    expect(api.put).toHaveBeenCalledTimes(1)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 6 })
  })

  it('marks the page in view as shown so it fades in', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()

    const sections = wrapper.findAll('section[data-page]')
    const observer = pageObserver()
    observer.fire([{ isIntersecting: true, target: sections[2].element, boundingClientRect: { top: 0 } }])
    await flushPromises()

    expect(sections[2].find('img').classes()).toContain('shown')
    expect(sections[0].find('img').classes()).not.toContain('shown')

    observer.fire([{ isIntersecting: false, target: sections[2].element, boundingClientRect: { top: 0 } }])
    await flushPromises()
    expect(sections[2].find('img').classes()).not.toContain('shown')
  })

  it('scrolls to a page chosen from the pager, rendering it first if it is outside the window', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()

    const target = wrapper.findAll('section[data-page]')[19].element
    const spy = vi.spyOn(target, 'scrollIntoView')

    wrapper.vm.setPage(20)
    await flushPromises()

    expect(wrapper.vm.rendered).toBe(20)
    expect(spy).toHaveBeenCalled()
  })

  it('disconnects both observers when it is unmounted', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()

    wrapper.unmount()

    expect(observers.every((observer) => observer.disconnected)).toBe(true)
  })

  it('commits the mode change and rebuilds the deck when switching back to one page at a time', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()

    await wrapper.vm.setMode('paged')
    await flushPromises()

    expect(store.commit).toHaveBeenCalledWith('setReaderMode', 'paged')
    expect(observers.every((observer) => observer.disconnected)).toBe(true)
    expect(reveal).toHaveBeenCalled()
    expect(wrapper.findAll('section[data-page]')).toHaveLength(30)
  })
})
