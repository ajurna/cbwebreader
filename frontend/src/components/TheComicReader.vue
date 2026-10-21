<template>
  <div class="reveal" :class="{ continuous: mode === 'scroll' }" id="comic_box" ref="comic_box">
    <div class="pane" :class="fit_class" ref="pane" :style="zoom_style">
      <div id="slides_div" class="slides" ref="slides">
        <section
          v-for="page in visible_pages"
          :key="page"
          :data-page="page"
          :data-menu-title="page"
          :hidden="mode === 'paged'"
          :style="ratio_style(page)"
        >
        <div class="page" :style="page_style(page)">
          <img
            :src="mode === 'scroll' ? image_url(page) : null"
            :data-src="mode === 'paged' ? image_url(page) : null"
            :loading="mode === 'scroll' ? 'lazy' : null"
            class="w-100"
            :alt="page"
          >
          <span class="page-mark" aria-hidden="true">{{ page }}</span>
        </div>
        </section>
      </div>
      <div class="sentinel" ref="sentinel" v-if="mode === 'scroll' && rendered < pages"></div>
    </div>
  </div>
  <div class="reading-progress" v-if="pages > 1">
    <div class="progress position-relative" role="progressbar" aria-label="Reading progress" :aria-valuenow="progress_percent" aria-valuemin="0" aria-valuemax="100">
      <div class="progress-bar" :style="'width: ' + progress_percent + '%;'"></div>
      <small class="justify-content-center d-flex position-absolute w-100 h-100 text-muted" style="line-height: normal">{{ progress_percent }}%</small>
    </div>
  </div>
  <div class="navButtons">
    <div class="nav-item pager" role="group" aria-label="Position in this comic" v-if="pages">
      <input
        type="number"
        ref="page_jump"
        class="page-field"
        aria-label="Page"
        :value="page_position"
        min="1"
        :max="pages"
        @change="jump_to_page"
      />
      <span class="text-muted small-text">&nbsp;/ {{ pages }}</span>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        title="Previous page"
        @click="prevPage()"
      >‹</button>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        title="Next page"
        @click="nextPage()"
      >›</button>
    </div>
    <div class="nav-item">
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        :title="'Read this comic ' + other_mode"
        @click="setMode(this.mode === 'paged' ? 'scroll' : 'paged')"
      >{{ other_mode }}</button>
    </div>
    <div class="nav-item" v-if="directory">
      <router-link
        class="btn btn-sm btn-outline-secondary ghost"
        :to="{ name: 'browse', params: { selector: directory } }"
        title="Back to this folder"
      >Folder</router-link>
    </div>
    <div class="nav-item">
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        :class="{ active: show_options }"
        :aria-pressed="show_options ? 'true' : 'false'"
        @click="show_options = !show_options"
      >?</button>
    </div>
  </div>
  <div class="options" v-if="show_options" role="dialog" aria-label="Reading options and keyboard shortcuts">
    <div class="options-head">
      <strong>Page size</strong>
      <button type="button" class="btn btn-sm btn-outline-secondary" @click="show_options = false">Close</button>
    </div>
    <div class="btn-group btn-group-sm" role="group" aria-label="Page size" v-if="mode === 'scroll'">
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        :class="{ active: fit === 'width' }"
        @click="set_fit('width')"
      >Fit width</button>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        :class="{ active: fit === 'page' }"
        @click="set_fit('page')"
      >Fit page</button>
    </div>
    <div class="btn-group btn-group-sm" role="group" aria-label="Zoom" v-if="mode === 'scroll'">
      <button type="button" class="btn btn-sm btn-outline-secondary" @click="zoom_by(-ZOOM_STEP)">−</button>
      <button type="button" class="btn btn-sm btn-outline-secondary" @click="zoom_by(ZOOM_STEP)">+</button>
    </div>
    <table>
      <tbody>
        <tr v-for="shortcut in shortcuts" :key="shortcut.keys">
          <td><kbd>{{ shortcut.keys }}</kbd></td>
          <td>{{ shortcut.action }}</td>
        </tr>
      </tbody>
    </table>
  </div>

</template>

<script>
import Reveal from "reveal.js";
import api from "@/api";
import Hammer from 'hammerjs'

// How many pages are rendered at a time in continuous mode. The window grows as the
// reader approaches the end of what has already been rendered.
const WINDOW_SIZE = 20;

// Pages fetched and decoded before the reader asks for them. In continuous mode the DOM
// images are `loading="lazy"`, so the browser would not start the next page until it is
// already close to the viewport, and a page still being scrolled to would pop in blank.
const PREFETCH_AHEAD = 2;
// The pane is always being scrolled, so what is asked for is a page that is already
// sliding in: fetching further ahead is what keeps its sheet from being blank.
const PANE_PREFETCH_AHEAD = 4;

// The page aspect ratio (width over height) used until a page reports its own. A
// definite height is needed before an image has loaded, so the length of the pane does
// not change as pages load.
const DEFAULT_PAGE_RATIO = 0.71;

// A pane is a real scroll container, so panning within a page is the browser's - the
// wheel, the scrollbar, a finger - rather than a key of ours.
const DEFAULT_PANE_HEIGHT = 1000;

// Zoom is a percentage of the fitted size, in these steps, within these bounds.
const ZOOM_STEP = 25;
const MIN_READER_ZOOM = 25;
const MAX_READER_ZOOM = 200;

// Held keys repeat, so a key press is handled immediately and then ignored for this
// long. The page write is already debounced by queue_save, so nothing is sent per key.
const KEY_THROTTLE_MS = 100;

export default {
  name: "TheComicReader",
  data () {
    return {
      current_page: 0,
      preloaded: new Map(),
      sizes: new Map(),
      deck: null,
      title: '',
      directory: '',
      prev_comic: {},
      next_comic: {},
      pages: 1,
      rendered: 0,
      visible: new Map(),
      page_observer: null,
      growth_observer: null,
      save_timeout: null,
      key_locked: false,
      key_timeout: null,
      show_options: false,
      shortcuts: [
        { keys: '← / →', action: 'Previous / next page' },
        { keys: '− / +', action: 'Zoom out / in' },
        { keys: 'Space', action: 'Next page' },
        { keys: 'Shift + Space', action: 'Previous page' },
        { keys: 'n / p', action: 'Next / previous page' },
        { keys: 'Home / End', action: 'First / last page' },
        { keys: 'm', action: 'Switch reading mode' },
        { keys: 'b', action: 'Back to this folder' },
        { keys: '?', action: 'Show or hide this list' },
        { keys: 'Esc', action: 'Hide this list' },
      ],
    }
  },
  props: {
    selector: String
  },
  computed: {
    mode () {
      return this.$store.state.reader_mode
    },
    set_read_url () {
      return '/api/read/' + this.selector + '/set_page/'
    },
    visible_pages () {
      if (this.mode === 'paged') {
        return Array.from({length: this.pages}, (_item, index) => index + 1)
      }
      return Array.from({length: Math.min(this.rendered, this.pages)}, (_item, index) => index + 1)
    },
    // The page being shown counts as reached, so a reader on page 3 of 10 is 30% through.
    progress_percent () {
      if (this.pages < 1) {
        return 0
      }
      return Math.round(Math.min(this.current_page + 1, this.pages) / this.pages * 100)
    },
    // Where the reader is in this comic, counted the way the progress is saved and a page
    // can be asked for, so the number on the screen is the number the reader can go back
    // to. The pages of a book with no pages at all - one that could not be read - start at
    // one rather than showing a page that does not exist.
    page_position () {
      if (this.pages < 1) {
        return 1
      }
      return Math.min(this.current_page + 1, this.pages)
    },
    // The bar carries one control for the reading mode. The mode in use is already what the
    // pages look like, so what the reader can ask for is the other one, named in plain
    // words rather than by the internal mode names.
    other_mode () {
      return this.mode === 'paged' ? 'in one stream' : 'one page at a time'
    },
    fit () {
      return this.$store.state.reader_fit === 'page' ? 'page' : 'width'
    },
    fit_class () {
      return 'fit-' + this.fit
    },
    zoom_percent () {
      const zoom = Number(this.$store.state.reader_zoom)
      if (!Number.isFinite(zoom)) {
        return 100
      }
      return Math.min(Math.max(zoom, MIN_READER_ZOOM), MAX_READER_ZOOM)
    },
    // The pane's own custom properties are what the sizing rules read, so a resized
    // window resizes the pages without any of this running again.
    zoom_style () {
      return '--page-zoom: ' + this.zoom_percent / 100
    }
  },
  methods: {
    image_url (page) {
      return '/api/read/' + this.selector + '/image/' + page + '/'
    },
    // One measured size per page, from whichever image reported first: the detached one
    // the warm up made, or the one that decoded in the pane. The box is reserved from the
    // real size, so the length of the pane does not change as pages load.
    record_size (page, image) {
      if (image.naturalWidth && image.naturalHeight && !this.sizes.has(page)) {
        this.sizes.set(page, {width: image.naturalWidth, height: image.naturalHeight})
      }
    },
    // A page's own aspect ratio, once its image has reported one. A method rather than
    // a computed: the page number is an argument, and the sizes are still read while the
    // page is being rendered, so a newly measured page redraws its box.
    page_ratio (page) {
      const measured = this.sizes.get(page)
      if (measured) {
        return measured.width / measured.height
      }
      // The pages of a book are one size, so any page already measured is a better
      // guess than the default, and the default only applies before the first one.
      const known = [...this.sizes.values()][0]
      if (known) {
        return known.width / known.height
      }
      return DEFAULT_PAGE_RATIO
    },
    ratio_style (page) {
      return '--page-ratio: ' + this.page_ratio(page)
    },
    // Only a size the page reported can be asked of its box. A box built from a guessed
    // ratio is where the page is squeezed: the page is drawn into the box it is given, so
    // a page that has not reported a size yet keeps its own, and its height comes from the
    // image. That is why the pane grows as a page enters it rather than holding a length
    // that is wrong for the page.
    page_style (page) {
      const measured = this.sizes.get(page)
      if (!measured) {
        // Nothing is asked of the box, so the page is drawn as the image has it.
        return null
      }
      return 'aspect-ratio: ' + measured.width / measured.height
    },
    // Detached <img> elements: setting src starts the fetch and the decode straight away,
    // and the element is kept in a Map so the bitmap is not collected before the page it
    // belongs to is reached. Same URL as the one that is shown, so nothing is fetched
    // twice.
    preload_pages (page) {
      const displayed = page + 1
      const ahead = this.mode === 'scroll' ? PANE_PREFETCH_AHEAD : PREFETCH_AHEAD
      for (let offset = 1; offset <= ahead; offset += 1) {
        const next = displayed + offset
        if (next <= this.pages && !this.preloaded.has(next)) {
          const image = document.createElement('img')
          image.src = this.image_url(next)
          // The measured size is what the page box is sized from: the pane is scrolled
          // by the height of the pages as they are drawn, so an assumed height that is
          // corrected later would move the reading position.
          image.onload = () => {
            this.record_size(next, image)
            // Decoding is what costs a frame, and it would otherwise happen the first
            // time the page is painted: asking for the bitmap here moves it off the
            // scroll. The element stays in the Map so the bitmap is kept, not recollected.
            if (image.decode) {
              image.decode()
            }
          }
          this.preloaded.set(next, image)
        }
      }
      // Pages at or behind the one being shown are dropped so a long book does not keep
      // every image it has fetched alive.
      for (const passed of [...this.preloaded.keys()]) {
        if (passed <= displayed) {
          this.preloaded.delete(passed)
        }
      }
    },
    set_fit (fit) {
      this.$store.commit('setReaderFit', fit)
    },
    zoom_by (step) {
      this.$store.commit('setReaderZoom', this.zoom_percent + step)
    },
    // How far a page's own middle is from the middle of the pane, used only for the times
    // the point being read falls in the gap between two sheets.
    distance_from_middle (rect, middle) {
      return Math.abs(rect.top + rect.height / 2 - middle)
    },
    // Where the middle of the pane is on the screen, for the times the observer is not
    // told the bounds of the root it was given.
    pane_box () {
      const pane = this.$refs.pane
      if (!pane) {
        return {top: 0, height: DEFAULT_PANE_HEIGHT}
      }
      const box = pane.getBoundingClientRect()
      return {top: box.top, height: box.height || DEFAULT_PANE_HEIGHT}
    },
    prevPage(behavior = 'smooth'){
      if (this.mode === 'scroll') {
        if (this.current_page <= 0) {
          this.prevComic()
        } else {
          this.current_page -= 1
          this.scroll_to_page(this.current_page + 1, behavior)
        }
        return
      }

      // reveal initializes asynchronously, so a key pressed before the promise resolves
      // has no deck to move.
      if (!this.deck) {
        return
      }

      if (this.deck.isFirstSlide()){
        this.prevComic()
      } else {
        this.current_page -= 1
        this.deck.slide(this.current_page)
        // Pages can be taller than the viewport, so show the top of the new page instead
        // of keeping the scroll offset left over from the previous one.
        this.scroll_to_page(this.current_page + 1, behavior)
      }
    },
    prevComic(){
      this.$router.push({
        name: this.prev_comic.route,
        params: {selector: this.prev_comic.selector}
      })
    },
    nextComic(){
      this.$router.push({
        name: this.next_comic.route,
        params: {selector: this.next_comic.selector}
      })
    },
    nextPage(behavior = 'smooth'){
      if (this.mode === 'scroll') {
        if (this.current_page + 1 >= this.pages) {
          this.nextComic()
        } else {
          this.current_page += 1
          this.scroll_to_page(this.current_page + 1, behavior)
        }
        return
      }

      if (!this.deck) {
        return
      }

      if (this.deck.isLastSlide()){
        this.nextComic()
      } else {
        this.current_page += 1
        this.deck.slide(this.current_page)
        this.scroll_to_page(this.current_page + 1, behavior)
      }
    },
    setPage(pageNum){
      if (this.mode === 'scroll') {
        const page = Math.min(pageNum, this.pages)
        // A jump leaves the end of the window at the page chosen, so the pages after it
        // would be added one at a time as the pan reached them, and each one arrives as a
        // blank sheet while it is fetched. The window is filled ahead of the jump instead,
        // the same way it is filled when the reader resumes at a page.
        this.rendered = Math.min(this.pages, Math.max(this.rendered, page + WINDOW_SIZE))
        this.current_page = page - 1
        this.$nextTick(() => {
          this.observe_pages()
          // A page chosen by number is what the reader wants to see, so the pane goes
          // to it rather than sliding through the pages between.
          this.scroll_to_page(page, 'instant')
        })
        return
      }

      if (!this.deck) {
        return
      }

      this.current_page = pageNum-1
      this.deck.slide(this.current_page)
      // The pages are laid out in the document, so the view has to move to the one that
      // was chosen as well as reveal being told about it: leaving the scroll where it was
      // shows the middle of a tall page instead of its top.
      this.scroll_to_page(pageNum, 'instant')
    },
    scroll_to_page (page, behavior = 'smooth') {
      const section = this.$refs.slides.querySelector('section[data-page="' + page + '"]')
      if (!section) {
        return
      }
      this.show_page(page)
      section.scrollIntoView({behavior: behavior, block: 'start'})
    },
    // A page the reader asked for is looked at straight away, so it must not wait for the
    // browser to notice that it is near enough: every page in the pane is inserted while
    // it is off screen, and after a jump a lazy one shows as a blank sheet. The pages after
    // it are the ones the pan brings in next, so their fetches start at the jump as well -
    // the same pages the warm up asks for ahead, so the fetch is shared.
    show_page (page) {
      for (let near = page - 1; near <= page + PANE_PREFETCH_AHEAD; near += 1) {
        const image = this.$refs.slides.querySelector('section[data-page="' + near + '"] img')
        if (image) {
          image.removeAttribute('loading')
        }
      }
    },
    // The page field in the bar is where the reader says a page starts: Vue writes the
    // field whenever the position changes, so the field only has to answer for a value the
    // reader typed, which is any value that is not already the page being read. A value
    // outside the comic's pages is not a page, so it is left alone and the field keeps
    // showing where the reader is.
    jump_to_page () {
      const field = this.$refs.page_jump
      if (!field) {
        return
      }
      const asked = Number(field.value)
      if (asked >= 1 && asked <= this.pages && asked !== this.current_page + 1) {
        this.setPage(asked)
      } else {
        // A page that is not one of this comic's is not a jump, and the field is put back
        // to where the reader is, so it never shows a page they are not on.
        field.value = this.page_position
      }
    },
    keyPress (e) {
      // Alt+Left is the browser's back button and Ctrl/Cmd+Arrow moves a caret in a
      // form control, so only a bare arrow key pages.
      if (e.ctrlKey || e.metaKey || e.altKey) {
        return
      }

      // These only show or hide the shortcut list, so they still work when a control
      // has focus.
      if (e.key === 'Escape') {
        this.show_options = false
        return
      }
      if (e.key === '?') {
        this.show_options = !this.show_options
        return
      }

      const key = e.key.toLowerCase()

      // The reader listens on window, so a key pressed while a text control has focus
      // would type as well as page. A focused button is left alone only for Space,
      // because Space activates the button - otherwise the keyboard stops working after
      // any click on the controls below the page.
      if (e.target && e.target.closest && e.target.closest('input, select, textarea')) {
        return
      }
      if (key === ' ' && e.target && e.target.closest && e.target.closest('button')) {
        return
      }

      if (this.key_locked) {
        return
      }
      this.key_locked = true
      this.key_timeout = setTimeout(() => { this.key_locked = false }, KEY_THROTTLE_MS)

      // Left and Right change pages; so do Space and n / p, which is what a keyboard
      // reader uses when a button has focus. Up and Down are not the component's: the
      // pane scrolls with the wheel, the scrollbar or a finger, and in one page at a
      // time the document scrolls the page - intercepting those keys there doubled up
      // with that scroll, and listing them next to the arrows for pages only read as
      // two ways of doing one thing.
      switch (key) {
        case 'arrowright':
        case 'n':
          this.nextPage('auto')
          return
        case 'arrowleft':
        case 'p':
          this.prevPage('auto')
          return
        case ' ':
          // Space would otherwise scroll the page as well as turning it.
          e.preventDefault?.()
          if (e.shiftKey) {
            this.prevPage('auto')
          } else {
            this.nextPage('auto')
          }
          return
        case 'home':
        case 'end':
          // Same for Home/End, which the browser would scroll to the page edges.
          e.preventDefault?.()
          this.setPage(key === 'home' ? 1 : this.pages)
          return
        case 'm':
          this.setMode(this.mode === 'paged' ? 'scroll' : 'paged')
          return
        case '-':
        case '_':
          this.zoom_by(-ZOOM_STEP)
          return
        case '+':
        case '=':
          this.zoom_by(ZOOM_STEP)
          return
        case 'b':
          if (this.directory) {
            this.$router.push({ name: 'browse', params: { selector: this.directory } })
          }
          return
      }
    },
    // Continuous mode: reveal is not used for visibility here, so the page in view is
    // worked out from what is actually intersecting the viewport.
    start_scroll () {
      this.visible.clear()

      const pane = this.$refs.pane
      // The pane clips what is shown, so the observer is told about the pane rather than
      // about the window: a page that has been scrolled out of the pane is not being read
      // even while its rectangle is still inside the window.
      const bounds = pane ? {root: pane} : {}
      this.page_observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            this.visible.set(entry.target, entry.boundingClientRect)
          } else {
            this.visible.delete(entry.target)
          }
        }

        if (this.visible.size === 0) {
          return
        }

        // The page being read is the one under the middle of the pane, which is where the
        // reader's eye is: the page covering that point is the page they are looking at.
        // A page's top reaching the top of the pane is not enough to make it current - at
        // that point the new page is only a strip at the bottom of the view, and the page
        // being left still holds the view - and a page that has not reached the middle yet
        // is not being read either. Where no page covers the middle, between two sheets, the
        // one whose own middle is nearer is the one in view.
        const root = entries[0].rootBounds || this.pane_box()
        const middle = root.top + root.height / 2
        const covering = [...this.visible.entries()].filter(
          ([, rect]) => rect.top <= middle && rect.top + rect.height > middle,
        )
        const in_view = covering.length
          ? covering[0][0]
          : [...this.visible.entries()].sort(
            (a, b) => this.distance_from_middle(a[1], middle) - this.distance_from_middle(b[1], middle),
          )[0][0]
        const page = Number(in_view.dataset.page)
        if (page && page !== this.current_page + 1) {
          this.current_page = page - 1
          this.queue_save(page - 1)
        }
      }, {threshold: 0, ...bounds})

      this.growth_observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          this.extend_window()
        }
      }, {rootMargin: '1200px 0px', ...bounds})

      this.observe_pages()
      if (this.$refs.sentinel) {
        this.growth_observer.observe(this.$refs.sentinel)
      }
      this.scroll_to_page(this.current_page + 1)
    },
    observe_pages () {
      this.$refs.slides.querySelectorAll('section[data-page]').forEach((section) => {
        const image = section.querySelector('img')
        // A page that has decoded in the pane has reported its real size, so its box is
        // reserved from that rather than from a guess.
        if (image) {
          this.record_size(Number(section.dataset.page), image)
        }
        this.page_observer.observe(section)
      })
    },
    extend_window () {
      if (this.rendered >= this.pages) {
        return
      }
      this.rendered = Math.min(this.pages, this.rendered + WINDOW_SIZE)
      this.$nextTick(() => this.observe_pages())
    },
    // One write per burst of scrolling rather than one per intersection.
    queue_save (page) {
      clearTimeout(this.save_timeout)
      this.save_timeout = setTimeout(() => {
        api.put(this.set_read_url, {page: page})
      }, 500)
    },
    start_paged () {
      this.deck = Reveal(this.$refs.comic_box)
      this.deck.initialize({
        controls: false,
        width: "100%",
        height: "100%",
        margin: 0,
        minScale: 1,
        maxScale: 1,
        keyboard: null,
        touch: false,
        transition: 'slide',
        embedded: true,
        plugins: [  ]
      }).then(() => {
        this.deck.slide(this.current_page)
        this.slideChanged = (event) => {
          this.$refs.comic_box.scrollIntoView({behavior: 'smooth'})
          api.put(this.set_read_url, {page: event.indexh})
        }
        this.deck.on('slidechanged', this.slideChanged);
      })
    },
    async setMode (mode) {
      if (mode === this.mode) {
        return
      }

      this.$store.commit('setReaderMode', mode)
      this.teardown()
      await this.$nextTick()

      if (mode === 'scroll') {
        this.rendered = Math.min(this.pages, Math.max(WINDOW_SIZE, this.current_page + 1))
        await this.$nextTick()
        this.start_scroll()
      } else {
        this.start_paged()
      }
    },
    teardown () {
      clearTimeout(this.save_timeout)
      this.preloaded.clear()

      if (this.page_observer) {
        this.page_observer.disconnect()
        this.page_observer = null
      }
      if (this.growth_observer) {
        this.growth_observer.disconnect()
        this.growth_observer = null
      }
      this.visible.clear()

      if (this.deck) {
        if (this.slideChanged) {
          this.deck.off('slidechanged', this.slideChanged)
        }
        try {
          this.deck.destroy()
        } catch (e) {
          console.log(e)
        }
        this.deck = null
      }
    }
  },
  watch: {
    'current_page' (new_page) {
      this.preload_pages(new_page)
    }
  },
  mounted () {
    let comic_data_url = '/api/read/' + this.selector + '/'
    window.addEventListener('keydown', this.keyPress)
    api.get(comic_data_url)
    .then(response => {
      this.title = response.data.title
      this.directory = response.data.directory || ''
      this.current_page = response.data.last_read_page
      this.prev_comic = response.data.prev_comic
      this.next_comic = response.data.next_comic
      this.pages = response.data.pages

      if (this.mode === 'scroll') {
        this.rendered = Math.min(this.pages, Math.max(WINDOW_SIZE, this.current_page + 1))
        return this.$nextTick().then(() => this.start_scroll())
      }
      return this.$nextTick().then(() => this.start_paged())
    })
    .then(() => {
      api.put(this.set_read_url, {page: this.current_page})
    })
    .catch((error) => {console.log(error)})

    this.hammertime = new Hammer(this.$refs.comic_box, {})
    this.hammertime.on('swipeleft', (_e, self=this) => {
      self.nextPage()
    })
    this.hammertime.on('swiperight', (_e, self=this) => {
      self.prevPage()
    })
    this.hammertime.on('tap', (_e, self=this) => {
      self.nextPage()
    })
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.keyPress)
    clearTimeout(this.key_timeout)
    this.teardown()
    try {
      this.hammertime.off('swipeleft')
      this.hammertime.off('swiperight')
      this.hammertime.off('tap')
    } catch (e) {
      console.log(e)
    }

  }
}
</script>


<style scoped>
/* The bar is one row that does not wrap: the controls it holds are few and each is
   narrow, so nothing here needs to scroll sideways. */
.navButtons {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 0;
    z-index: 1030;
  width: auto;
  max-width: 100vw;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  cursor: pointer;
}

/* What the page field is grouped with: the count of pages next to the page number makes
   the position readable as a position rather than as a number on its own. */
.pager {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* The progress bar is at the top centre, away from the controls, because the page fills
   the middle of the screen and the bar must not compete with it; the light backdrop is
   the one the settings panel uses, so it stays legible over artwork, and pointer-events:
   none leaves the page underneath clickable and scrollable. */
.reading-progress {
  position: fixed;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 160px;
  padding: 4px 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1030;
  pointer-events: none;
  cursor: default;
}

/* The link back to the folder is always there but stays quiet until it is hovered or
   focused, so it does not compete with the page. */
.ghost {
  opacity: 0.45;
}

.ghost:hover,
.ghost:focus {
  opacity: 1;
}
section {
  padding-bottom: 60px;
}

.options {
  position: fixed;
  right: 12px;
  bottom: 64px;
  max-width: 340px;
  padding: 10px 12px;
  border: 1px solid #adb5bd;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.95);
  font-size: 0.85rem;
  z-index: 20;
}

.options-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.options td {
  padding: 2px 8px 2px 0;
  vertical-align: top;
}

.options kbd {
  font-family: inherit;
  white-space: nowrap;
}

/* The page field is part of the readout, not a control that stands on its own: it takes
   the bar's colours so the position reads as one line, and it is wide enough that a
   three digit page number does not push the count of pages along. */
.page-field {
  border: 0;
  background: transparent;
  box-shadow: none;
  color: inherit;
  font: inherit;
  padding: 0;
  margin: 0 6px 0 0;
  min-width: 2.5em;
}

/* reveal.css is deliberately not loaded, so visibility is the `hidden` attribute and
   reveal's own transition classes do nothing. A transition cannot run across
   display:none -> block, so paged mode uses an animation on the slide that becomes
   present; continuous mode uses a transition driven by the IntersectionObserver. */
.reveal section.present img {
  animation: page-fade 0.3s ease;
}

/* The pane is a scroll container, so the wheel, the touch drag and the scrollbar all
   work inside it and what it scrolls is the height of the pages as they are drawn.
   It starts below the progress bar and stops above the row of controls, which is where
   the bottom bar sits: the inset is the height of each, so neither covers a page. */
.continuous .pane {
  --pane-w: 100vw;
  --pane-h: calc(100vh - 96px);
  --page-ratio: 0.71;
  --page-zoom: 1;
  position: fixed;
  top: 40px;
  left: 0;
  right: 0;
  bottom: 56px;
  overflow-y: auto;
  z-index: 1;
}

/* Every page is a box of its own rather than a loose image in the flow, so the number of
   the page can be drawn where the page is: a number pinned to the pane would sit over a
   neighbouring page whenever this one is narrower than the window it is shown in. The box
   is what is sized, and the image fills it. */
.reveal .page {
  position: relative;
}

/* The box is what the pane sizes, and the image fills it at its own shape: sizing the
   box rather than the image is what lets a page be marked with its own number, and what
   leaves the image undistorted - only a box the page reported a height for is asked of it.
   The image is a block so it does not sit on a text baseline inside its box. */
.continuous .pane .page img {
  display: block;
  height: auto;
}

.continuous .pane.fit-width .page {
  width: calc(var(--pane-w) * var(--page-zoom));
}

/* Fit page is the widest a page can be and still be seen whole: the pane height times
   the page aspect ratio, or the pane width when that is narrower. */
.continuous .pane.fit-page .page {
  width: min(calc(var(--pane-w) * var(--page-zoom)), calc(var(--pane-h) * var(--page-ratio) * var(--page-zoom)));
}

/* The page number is a stamp on the sheet it belongs to, in the corner where the reader
   looks for it. The digits are translucent so they sit with the artwork rather than as a
   panel over it, and the halo behind them is what carries the contrast - on a pale page
   the translucent digits alone would be the colour of the page. The size does not follow
   the zoom: this is a corner mark, and one that grew with the page would end up covering
   the art it is written over, and it stays at the page's corner wherever the reader is.
   It is not interactive, and it is hidden from readers who are told the page number by
   the image's own description. */
.reveal .page-mark {
  position: absolute;
  top: 8px;
  left: 10px;
  color: rgba(255, 255, 255, 0.6);
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.85), 0 1px 1px rgba(0, 0, 0, 0.6);
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
  pointer-events: none;
}

/* A page is centred when it is narrower than the pane, and the gutter between pages is
   only what keeps two from touching: the clearance from the controls is the pane's inset.
   The 60px below a page is for paged mode, where the page scrolls in the document. */
.continuous .pane section {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-bottom: 12px;
}

/* Nothing snaps here on purpose. A snap area is the size of a page, so proximity would
   take the next page edge as soon as a pan starts and hold the reader there: that hold
   is the freeze the reader feels between pages, not a page settling into place. A page
   chosen from the pager is aligned by scrolling its section to the top of the pane, which
   is exact with or without snapping. */

/* The pane does not fade its pages: a sheet that is half transparent while it slides in
   is read as a blank gap, and the page being solid the moment it is in the pane is the
   point of the pane. What is late is the fetch and the decode, and both are asked for
   ahead of the reader above. One page at a time still fades, because there the page is
   swapped rather than moved. */

@keyframes page-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .reveal section.present img {
    animation: none;
  }
}
</style>
