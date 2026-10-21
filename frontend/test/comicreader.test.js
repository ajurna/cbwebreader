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
  directory: 'd1',
  prev_comic: { route: 'browse', selector: 'p1' },
  next_comic: { route: 'browse', selector: 'n1' },
}

const mounted = []

function mountReader() {
  const wrapper = mount(TheComicReader, {
    props: { selector: 'a1' },
    global: {
      mocks: { $router: router, $store: store },
      stubs: {
        RouterLink: { props: ['to'], template: '<a class="folder-link" :data-selector="to.params.selector"><slot /></a>' },
      },
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
    // The reader settings are kept the way the store keeps them, so a test that asks
    // for a size can see the page sizing follow it.
    if (name === 'setReaderFit' && (value === 'width' || value === 'page')) {
      store.state.reader_fit = value
    }
    if (name === 'setReaderZoom') {
      store.state.reader_zoom = Math.min(Math.max(Number(value), 25), 200)
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

  it('keeps the position in the bar in step with the deck', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.setPage(4)
    expect(deck.slide).toHaveBeenCalledWith(3)
    await flushPromises()
    // The number the reader sees is the page they are on, so a page asked for later can
    // name it - which is the page progress is saved against.
    expect(wrapper.find('.page-field').attributes('value')).toBe('4')
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

  it('ignores keys pressed while a text control has focus', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    wrapper.vm.keyPress({ key: 'ArrowRight', target: document.createElement('input') })
    expect(deck.slide).not.toHaveBeenCalled()
  })

  it('still pages when a button has focus but leaves Space to that button', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    const button = document.createElement('button')
    wrapper.vm.keyPress({ key: 'ArrowRight', target: button })
    wrapper.vm.keyPress({ key: 'ArrowRight', target: button })
    expect(deck.slide).toHaveBeenCalledTimes(1)
    expect(deck.slide).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: ' ', target: button, preventDefault: vi.fn() })
    expect(deck.slide).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: ' ', target: document.body, preventDefault: vi.fn() })
    expect(deck.slide).toHaveBeenCalledTimes(2)
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

  it('shows the reading options with ? and hides them again', async () => {
    const wrapper = mountReader()
    await flushPromises()

    expect(wrapper.find('.options').exists()).toBe(false)

    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    expect(wrapper.find('.options').exists()).toBe(true)

    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    expect(wrapper.find('.options').exists()).toBe(false)
  })

  it('hides the reading options with Escape even when a control has focus', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    expect(wrapper.find('.options').exists()).toBe(true)

    wrapper.vm.keyPress({ key: 'Escape', target: document.createElement('input') })
    await flushPromises()
    expect(wrapper.find('.options').exists()).toBe(false)
  })

  it('toggles the reading options from the ? button', async () => {
    const wrapper = mountReader()
    await flushPromises()

    const button = wrapper.find('button[aria-pressed]')
    await button.trigger('click')
    expect(wrapper.find('.options').exists()).toBe(true)
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

  it('records the page holding the middle of the pane, not the one highest on the screen', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    // The page being read is the one under the middle of the pane. A page whose top is the
    // highest on the screen is only a strip at the bottom of the view, so it is not being
    // read yet; the page covering the middle is.
    pageObserver().fire([
      { isIntersecting: true, target: sections[4].element, boundingClientRect: { top: -1200, height: 1400 } },
      { isIntersecting: true, target: sections[5].element, boundingClientRect: { top: 200, height: 1400 } },
    ])

    expect(wrapper.vm.current_page).toBe(5)
    vi.advanceTimersByTime(500)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 5 })
  })

  it('keeps the recorded page while scrolling inside a page taller than the viewport', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    const observer = pageObserver()
    observer.fire([{ isIntersecting: true, target: sections[4].element, boundingClientRect: { top: 0, height: 1400 } }])
    vi.advanceTimersByTime(500)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 4 })

    // Panning within that page leaves its own middle still on the one being read, so
    // nothing is written.
    api.put.mockClear()
    observer.fire([{ isIntersecting: true, target: sections[4].element, boundingClientRect: { top: -300, height: 1400 } }])
    vi.advanceTimersByTime(500)
    expect(wrapper.vm.current_page).toBe(4)
    expect(api.put).not.toHaveBeenCalled()

    // The recorded page only changes when the next page becomes the one in view.
    observer.fire([
      { isIntersecting: false, target: sections[4].element },
      { isIntersecting: true, target: sections[5].element, boundingClientRect: { top: 0, height: 1400 } },
    ])
    vi.advanceTimersByTime(500)
    expect(wrapper.vm.current_page).toBe(5)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 5 })
  })

  it('hands the page over where the next one holds the middle of the pane', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    const observer = pageObserver()
    // A pan moves the pages up, so the page being left still has its top above the top of
    // the pane and is still partly in view. The page whose own middle is on the middle of
    // the pane is the one being read - taking the page whose top is the highest on the
    // screen is what writes the page being left, and the number in the bar returns to
    // where it was, which the reader did not ask for.
    observer.fire([
      { isIntersecting: true, target: sections[4].element, boundingClientRect: { top: -400, height: 1400 } },
      { isIntersecting: true, target: sections[5].element, boundingClientRect: { top: 1000, height: 1400 } },
    ])
    vi.advanceTimersByTime(500)
    expect(wrapper.vm.current_page).toBe(4)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 4 })

    // Panning on pushes the page being left past the middle of the pane and brings the
    // next one over it, which is where the page changes.
    observer.fire([
      { isIntersecting: true, target: sections[4].element, boundingClientRect: { top: -1200, height: 1400 } },
      { isIntersecting: true, target: sections[5].element, boundingClientRect: { top: 200, height: 1400 } },
    ])
    vi.advanceTimersByTime(500)
    expect(wrapper.vm.current_page).toBe(5)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 5 })
  })

  it('asks a step for a view rather than for a page, so the number is the page in view', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const before = wrapper.vm.current_page
    const target = wrapper.findAll('section[data-page]')[before + 1].element
    const moved = vi.spyOn(target, 'scrollIntoView')

    wrapper.vm.nextPage()
    await flushPromises()

    // A step names a page, so the view is placed at it rather than gliding there: the
    // only smooth movement is the reader's own pan, which the browser runs.
    expect(moved).toHaveBeenCalledWith({ behavior: 'instant', block: 'start' })
    // The step only moves the pane. A scroll this file runs changes no page's
    // intersection, so the page observer is never told the view moved, and its numbers
    // still describe the page being left - writing a page from the step as well would
    // write a number the view was asked for, not one the view holds.
    expect(wrapper.vm.current_page).toBe(before)
    expect(wrapper.find('.page-field').attributes('value')).toBe(String(before + 1))

    // What the pane holds once it is there decides the page: the page stepped to covers
    // the middle of the view and the page being left no longer does.
    const observer = pageObserver()
    const sections = wrapper.findAll('section[data-page]')
    observer.fire([
      { isIntersecting: false, target: sections[before].element },
      { isIntersecting: true, target: sections[before + 1].element, boundingClientRect: { top: 0, height: 1400 } },
    ])
    await flushPromises()
    expect(wrapper.vm.current_page).toBe(before + 1)
    expect(wrapper.find('.page-field').attributes('value')).toBe(String(before + 2))
    vi.advanceTimersByTime(500)
    expect(api.put).toHaveBeenCalledTimes(1)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: before + 1 })
  })

  it('writes once for a burst of scrolling rather than once per intersection', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()
    api.put.mockClear()

    const sections = wrapper.findAll('section[data-page]')
    const observer = pageObserver()
    observer.fire([{ isIntersecting: true, target: sections[5].element, boundingClientRect: { top: -1000, height: 1400 } }])
    observer.fire([{ isIntersecting: true, target: sections[6].element, boundingClientRect: { top: 400, height: 1400 } }])
    vi.advanceTimersByTime(500)

    expect(api.put).toHaveBeenCalledTimes(1)
    expect(api.put).toHaveBeenCalledWith('/api/read/a1/set_page/', { page: 6 })
  })

  it('keeps the pages it holds visible, so nothing is revealed as it slides in', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()

    const sections = wrapper.findAll('section[data-page]')
    expect(sections[2].find('img').element.getAttribute('src')).to.contain('/api/read/')
    expect(sections[2].find('img').classes()).to.not.include('shown')

    // What is in the pane is drawn as it enters, so observing a page changes what is
    // being read, never what can be seen.
    const observer = pageObserver()
    observer.fire([{ isIntersecting: true, target: sections[2].element, boundingClientRect: { top: 0, height: 1400 } }])
    await flushPromises()
    expect(wrapper.html()).to.not.contain('shown')
  })

  it('scrolls to a page chosen from the pager, rendering what the jump reaches first', async () => {
    const wrapper = mountContinuous(30)
    await flushPromises()

    const target = wrapper.findAll('section[data-page]')[19].element
    const spy = vi.spyOn(target, 'scrollIntoView')

    wrapper.vm.setPage(20)
    await flushPromises()

    expect(spy).toHaveBeenCalled()
    expect(wrapper.vm.rendered).toBe(30)
    expect(wrapper.findAll('section[data-page]')).toHaveLength(30)
  })

  it('fills the window ahead of a jump instead of adding pages as the pan reaches them', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    wrapper.vm.setPage(12)
    await flushPromises()

    // A window of pages past the page chosen is in the pane, so reading on from a jump
    // shows sheets that are already there and being fetched, rather than one blank page at
    // a time as the pane grew.
    expect(wrapper.vm.rendered).toBe(32)
    expect(wrapper.findAll('section[data-page]')).toHaveLength(32)
  })

  it('starts the page it jumps to loading, since it was put in the pane off screen', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    const imgs = wrapper.findAll('img')
    expect(imgs[11].element.getAttribute('loading')).toBe('lazy')

    wrapper.vm.setPage(12)
    await flushPromises()

    // The page asked for and the pages after it are read straight away, so their fetches
    // start at the jump; a page beyond that band keeps its lazy hint, so a jump does not
    // fetch the book up to that page.
    const moved = wrapper.findAll('img')
    expect(moved[10].element.getAttribute('loading')).toBe(null)
    expect(moved[11].element.getAttribute('loading')).toBe(null)
    expect(moved[15].element.getAttribute('loading')).toBe(null)
    expect(moved[16].element.getAttribute('loading')).toBe('lazy')
    expect(moved[17].element.getAttribute('loading')).toBe('lazy')
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

describe('TheComicReader back to the folder', () => {
  it('links to the folder the book is in', async () => {
    const wrapper = mountReader()
    await flushPromises()
    expect(wrapper.find('.folder-link').attributes('data-selector')).toBe('d1')
  })

  it('does not show the link for a book that is not in a folder', async () => {
    api.get.mockResolvedValue({ data: { ...COMIC, directory: null } })
    const wrapper = mountReader()
    await flushPromises()
    expect(wrapper.find('.folder-link').exists()).toBe(false)
  })

  it('returns to the folder with b', async () => {
    const wrapper = mountReader()
    await flushPromises()
    wrapper.vm.keyPress({ key: 'b', target: document.createElement('div') })
    expect(router.push).toHaveBeenCalledWith({ name: 'browse', params: { selector: 'd1' } })
  })
})

describe('TheComicReader preloading', () => {
  it('fetches the pages after the one being shown', async () => {
    const wrapper = mountReader()
    await flushPromises()

    // The fixture is on page 3 of 5, so pages 4 and 5 are the ones ahead of it.
    expect(Array.from(wrapper.vm.preloaded.keys())).toEqual([4, 5])
  })

  it('leaves nothing to fetch at the last page', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.setPage(5)
    await flushPromises()
    expect(Array.from(wrapper.vm.preloaded.keys())).toEqual([])

    wrapper.vm.setPage(1)
    await flushPromises()
    expect(Array.from(wrapper.vm.preloaded.keys())).toEqual([2, 3])
  })

  it('drops the images it fetched when the reader is torn down', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.setMode('scroll')
    await flushPromises()
    expect(Array.from(wrapper.vm.preloaded.keys())).toEqual([])
  })
})

describe('TheComicReader progress', () => {
  it('shows the share of the book that has been reached', async () => {
    const wrapper = mountReader()
    await flushPromises()

    // The fixture is on page 3 of 5.
    expect(wrapper.find('.reading-progress').exists()).toBe(true)
    expect(wrapper.find('[role="progressbar"]').attributes('aria-valuenow')).toBe('60')
    expect(wrapper.text()).toContain('60%')
    expect(wrapper.find('.progress-bar').attributes('style')).toContain('width: 60%;')

    // The bar is a sibling of the bottom bar, not one of its controls, so it sits at the
    // top of the screen instead of joining the row of buttons.
    expect(wrapper.element.querySelector('.navButtons').querySelector('.reading-progress')).toBe(null)
  })

  it('counts the page being shown as reached', async () => {
    const wrapper = mountReader()
    await flushPromises()

    wrapper.vm.setPage(5)
    await flushPromises()
    expect(wrapper.find('[role="progressbar"]').attributes('aria-valuenow')).toBe('100')

    wrapper.vm.setPage(1)
    await flushPromises()
    expect(wrapper.find('[role="progressbar"]').attributes('aria-valuenow')).toBe('20')
  })

  it('leaves the bar out of a book that cannot show progress', async () => {
    api.get.mockResolvedValue({ data: { ...COMIC, pages: 1 } })
    const wrapper = mountReader()
    await flushPromises()

    expect(wrapper.find('.reading-progress').exists()).toBe(false)
  })
})

describe('TheComicReader bottom bar', () => {
  it('keeps every control on one line instead of using a wrapping Bootstrap row', async () => {
    const wrapper = mountReader()
    await flushPromises()

    const bar = wrapper.find('.navButtons')
    expect(bar.classes()).not.toContain('row')

    // A position in the comic, the one control for the reading mode, the way back to the
    // folder, and the trigger for the settings: the page list, both page-size groups and
    // the mode buttons that used to stand here are each said by something else.
    const controls = bar.findAll('.nav-item')
    expect(controls).toHaveLength(4)
    expect(controls.map((item) => item.element.parentElement)).toEqual(controls.map(() => bar.element))
    const buttons = bar.findAll('button').map((button) => button.text())
    expect(buttons).to.include('‹')
    expect(buttons).to.include('›')
    expect(buttons).to.not.include('One page')
    expect(buttons).to.not.include('Fit width')
    expect(bar.find('.page-field').exists()).toBe(true)
  })

  it('shows where the reader is and takes a page from a field', async () => {
    const wrapper = mountReader()
    await flushPromises()

    // The readout is the position the reader is at, in the same pages the progress is
    // saved in, so it cannot disagree with what happens when they return.
    const field = wrapper.find('.page-field')
    // The fixture's comic was read up to page 2, so the reader resumes on page 3 and that
    // is what the field and the readout show.
    expect(field.attributes('value')).toBe('3')
    expect(wrapper.element.querySelector('.nav-item.pager').textContent).to.contain('/ 5')
  })

  it('jumps to a page the reader types into the field', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    const input = wrapper.find('.page-field')
    // Vue only fires the change handler for a value the reader supplies, which is any value
    // other than the page being read - so it is only ever asked for those.
    const typed = input.element
    typed.value = 5
    typed.dispatchEvent(new Event('change'))
    await flushPromises()

    // One page at a time, reveal is told the page in one step rather than walked through
    // the pages between, and the view moves there instantly.
    expect(deck.slide).toHaveBeenCalledTimes(1)
    expect(wrapper.vm.current_page).toBe(4)
    // The readout and the field follow the jump, so a reader who types a page sees the
    // page they are on - which is what is saved when they return. The count of this
    // comic's pages is next to the number, so the position cannot be read out of context.
    expect(input.attributes('value')).toBe('5')
    expect(wrapper.element.querySelector('.nav-item.pager').textContent).to.contain('/ 5')
  })

  it('leaves a page that is not in this comic alone', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()

    const typed = wrapper.find('.page-field').element
    typed.value = 999
    typed.dispatchEvent(new Event('change'))
    await flushPromises()

    // A value outside the comic's pages is not a page, so the reader is not moved, and the
    // field is put back to where they are.
    expect(deck.slide).toHaveBeenCalledTimes(0)
    expect(wrapper.vm.current_page).toBe(2)
    expect(typed.value).toBe('3')
  })

  it('asks for the other way of reading, and keeps a position when the mode changes', async () => {
    const wrapper = mountReader()
    await flushPromises()
    store.state.reader_mode = 'paged'

    const buttons = wrapper.findAll('button')
    const button = buttons.find((item) => item.text() === 'in one stream')
    expect(button.text()).toBe('in one stream')
    await button.trigger('click')
    await flushPromises()

    expect(store.commit).toHaveBeenCalledWith('setReaderMode', 'scroll')
    expect(store.state.reader_mode).toBe('scroll')
    // Changing how the pages are read does not move the reader, so the position shown is
    // still the page they were on before.
    expect(wrapper.find('.page-field').attributes('value')).toBe('3')
  })

  it('asks for the page number through a text field, so the browser adds no arrows of its own', async () => {
    const wrapper = mountReader()
    await flushPromises()
    const field = wrapper.find('.page-field')

    // A number field grows a spin of its own - the up and down arrows the browser draws
    // over it - which is a second way of moving pages next to the arrows in this row and
    // the pane's own scroll, so the digits are read from a text field and checked here.
    expect(field.attributes('type')).toBe('text')
    expect(field.attributes('inputmode')).toBe('numeric')
  })

  it('leaves anything the reader types that is not a page alone', async () => {
    const wrapper = mountReader()
    await flushPromises()
    deck.slide.mockClear()
    const typed = wrapper.find('.page-field').element

    typed.value = 'banana'
    typed.dispatchEvent(new Event('change'))
    await flushPromises()
    typed.value = '2.5'
    typed.dispatchEvent(new Event('change'))
    await flushPromises()

    // A text field takes whatever is typed, so a word and a half a page are not pages:
    // the reader is not moved and the field goes back to where they are.
    expect(deck.slide).toHaveBeenCalledTimes(0)
    expect(wrapper.vm.current_page).toBe(2)
    expect(typed.value).toBe('3')
  })
})

describe('TheComicReader in a pane', () => {
  function mountContinuous(pageCount) {
    store.state.reader_mode = 'scroll'
    api.get.mockResolvedValue({ data: { ...COMIC, pages: pageCount } })
    return mountReader()
  }

  // The pane is moved by assigning scrollTop, so the test records what it is asked for
  // and what it was last at.
  function trackScrolling(wrapper) {
    const pane = wrapper.find('.pane').element
    const scrolled = []
    Object.defineProperty(pane, 'scrollTop', {
      get: () => (scrolled.length ? scrolled[scrolled.length - 1] : 0),
      set: (position) => { scrolled.push(position) },
    })
    return scrolled
  }

  it('scrolls the pages inside a pane of their own, sized by the screen', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    const pane = wrapper.find('.pane')
    expect(pane.classes()).to.include('fit-width')
    expect(pane.element.getAttribute('style')).to.contain('--page-zoom: 1')
    // The pane is only a scroller in this mode; the reveal root is what marks the mode,
    // and the sizing rules are hung under it.
    expect(pane.element.parentElement.getAttribute('class')).to.contain('continuous')

    // A page has a height before it has loaded, so the length of the pane does not
    // change as pages load - only the width is guessed at then, never the shape of a page.
    expect(wrapper.find('section[data-page="2"]').element.getAttribute('style')).to.contain('--page-ratio')
    // Nothing has reported a size yet, so no ratio is asked of a page: a box from a guess
    // is what shows a page squeezed rather than as drawn.
    expect(wrapper.find('img').element.getAttribute('style')).toBe(null)
  })

  it('sizes a page only from a size the image reported, so a page is drawn as it is', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    wrapper.vm.record_size(3, {naturalWidth: 1200, naturalHeight: 1600})
    expect(wrapper.vm.page_ratio(3)).toBeCloseTo(0.75)
    expect(wrapper.vm.page_style(3)).toBe('aspect-ratio: 0.75')
    // The pages of a book are one size, so a size that was reported is a good guess for
    // the width of the rest - but only the width: the shape of an unmeasured page is left
    // to the image, so it is never stretched into a guessed box.
    expect(wrapper.vm.page_ratio(4)).toBeCloseTo(0.75)
    expect(wrapper.vm.page_style(4)).toBeNull()
  })

  it('marks the sheet it is on with the page it is on, in both readings', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    // A page is a box of its own now, so the mark is asked of the box rather than of the
    // row: in fit page a page is narrower than the pane, and a number that belonged to
    // the pane would sit over the neighbouring page.
    const third = wrapper.find('section[data-page="3"]').element
    const mark = third.querySelector('.page-mark')
    expect(mark.textContent).toBe('3')
    // Only the pages that are rendered are marked, so the numbers in the pane are the
    // pages in it - which is what the reader is asked to trust.
    expect(wrapper.findAll('.page-mark')).toHaveLength(wrapper.findAll('section[data-page]').length)
  })

  it('pans within the page with the arrow keys, which the browser would not scroll', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()
    const scrolled = trackScrolling(wrapper)

    wrapper.vm.keyPress({ key: 'ArrowDown', preventDefault: vi.fn() })
    await flushPromises()
    expect(scrolled).toEqual([400])

    vi.advanceTimersByTime(100)
    wrapper.vm.keyPress({ key: 'ArrowUp', preventDefault: vi.fn() })
    await flushPromises()
    expect(scrolled).toEqual([400, 0])
  })

  it('leaves the arrow keys alone when one page at a time is shown', async () => {
    const wrapper = mountReader()
    await flushPromises()
    const scrolled = trackScrolling(wrapper)

    wrapper.vm.keyPress({ key: 'ArrowDown', preventDefault: vi.fn() })
    await flushPromises()
    expect(scrolled).toEqual([])
    expect(wrapper.vm.$refs.pane.parentElement.getAttribute('class')).to.not.contain('continuous')
  })

  it('keeps the page size and the zoom out of the way until a pane is being scrolled', async () => {
    const paged = mountReader()
    await flushPromises()
    // In one page at a time the deck sizes the page and there is nothing to pan or zoom,
    // so the settings that would do nothing are not offered.
    const pagedButtons = paged.findAll('button').map((button) => button.text())
    expect(pagedButtons).to.not.include('Fit page')
    expect(paged.find('.options').exists()).toBe(false)

    const wrapper = mountContinuous(45)
    await flushPromises()
    // They are offered when the options are shown, which is where they live now: a setting
    // that is not being used does not need to stand in the bar all the time.
    wrapper.vm.keyPress({ key: '?' })
    await flushPromises()
    const buttons = wrapper.findAll('button').map((button) => button.text())
    expect(buttons).to.contain('Fit width')
    expect(buttons).to.contain('Fit page')
  })

  it('draws the whole page when asked to', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    wrapper.vm.set_fit('page')
    await flushPromises()
    expect(store.commit).toHaveBeenCalledWith('setReaderFit', 'page')
    expect(wrapper.vm.fit).toBe('page')
    expect(wrapper.find('.pane').classes()).to.contain('fit-page')
  })

  it('zooms within bounds and the pane follows', async () => {
    const wrapper = mountContinuous(45)
    await flushPromises()

    wrapper.vm.keyPress({ key: '+' })
    await flushPromises()
    expect(store.commit).toHaveBeenCalledWith('setReaderZoom', 125)
    expect(wrapper.find('.pane').element.getAttribute('style')).to.contain('--page-zoom: 1.25')

    // The step is what is asked for; the bounds are what is kept.
    wrapper.vm.zoom_by(200)
    await flushPromises()
    expect(store.commit).toHaveBeenLastCalledWith('setReaderZoom', 325)
    expect(wrapper.find('.pane').element.getAttribute('style')).to.contain('--page-zoom: 2')
  })

  it('fetches the pages that are about to slide in, further than one page at a time', async () => {
    const wrapper = mountContinuous(8)
    await flushPromises()

    // The fixture is on page 3 of 8, so four pages ahead of it are fetched; one page
    // at a time fetches two, because reveal's own lazy loader covers the rest.
    expect(Array.from(wrapper.vm.preloaded.keys())).toEqual([4, 5, 6, 7])
  })
})
