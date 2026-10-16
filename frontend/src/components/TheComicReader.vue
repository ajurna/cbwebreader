<template>
  <div class="reveal" :class="{ continuous: mode === 'scroll' }" id="comic_box" ref="comic_box">
    <div id="slides_div" class="slides" ref="slides">
      <section
        v-for="page in visible_pages"
        :key="page"
        :data-page="page"
        :data-menu-title="page"
        :hidden="mode === 'paged'"
      >
        <img
          :class="{ shown: mode === 'scroll' && inview.has(page) }"
          :src="mode === 'scroll' ? image_url(page) : null"
          :data-src="mode === 'paged' ? image_url(page) : null"
          :loading="mode === 'scroll' ? 'lazy' : null"
          class="w-100"
          :alt="page"
        >
      </section>
    </div>
    <div class="sentinel" ref="sentinel" v-if="mode === 'scroll' && rendered < pages"></div>
  </div>
  <div class="row navButtons pb-2">
    <div class="col-auto">
      <div class="btn-group btn-group-sm" role="group" aria-label="Reading mode">
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: mode === 'paged' }"
          @click="setMode('paged')"
        >One page</button>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: mode === 'scroll' }"
          @click="setMode('scroll')"
        >Continuous</button>
      </div>
    </div>
    <div class="col-auto">
      <comic-paginate
        v-model="paginate_page"
        :page_count="pages"
        @setPage="this.setPage"
        @prevComic="prevComic"
        @nextComic="nextComic"
      />
    </div>
    <div class="col-auto">
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary"
        :class="{ active: show_shortcuts }"
        :aria-pressed="show_shortcuts ? 'true' : 'false'"
        @click="show_shortcuts = !show_shortcuts"
      >?</button>
    </div>
  </div>
  <div class="shortcuts" v-if="show_shortcuts" role="dialog" aria-label="Keyboard shortcuts">
    <div class="shortcuts-head">
      <strong>Keyboard shortcuts</strong>
      <button type="button" class="btn btn-sm btn-outline-secondary" @click="show_shortcuts = false">Close</button>
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
import ComicPaginate from "@/components/ComicPaginate";

// How many pages are rendered at a time in continuous mode. The window grows as the
// reader approaches the end of what has already been rendered.
const WINDOW_SIZE = 20;

// Held keys repeat, so a key press is handled immediately and then ignored for this
// long. The page write is already debounced by queue_save, so nothing is sent per key.
const KEY_THROTTLE_MS = 100;

export default {
  name: "TheComicReader",
  components: {ComicPaginate},
  data () {
    return {
      current_page: 0,
      paginate_page: 1,
      inview: new Set(),
      deck: null,
      title: '',
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
      show_shortcuts: false,
      shortcuts: [
        { keys: '← / →', action: 'Previous / next page' },
        { keys: '↑ / ↓', action: 'Scroll within the page' },
        { keys: 'Space', action: 'Next page' },
        { keys: 'Shift + Space', action: 'Previous page' },
        { keys: 'n / p', action: 'Next / previous page' },
        { keys: 'Home / End', action: 'First / last page' },
        { keys: 'm', action: 'Switch reading mode' },
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
    }
  },
  methods: {
    image_url (page) {
      return '/api/read/' + this.selector + '/image/' + page + '/'
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
        this.rendered = Math.max(this.rendered, page)
        this.current_page = page - 1
        this.$nextTick(() => {
          this.observe_pages()
          this.scroll_to_page(page)
        })
        return
      }

      if (!this.deck) {
        return
      }

      this.current_page = pageNum-1
      this.deck.slide(this.current_page)
    },
    scroll_to_page (page, behavior = 'smooth') {
      const section = this.$refs.slides.querySelector('section[data-page="' + page + '"]')
      if (section) {
        section.scrollIntoView({behavior: behavior, block: 'start'})
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
        this.show_shortcuts = false
        return
      }
      if (e.key === '?') {
        this.show_shortcuts = !this.show_shortcuts
        return
      }

      // The reader listens on window, so a key pressed while a control has focus would
      // otherwise page as well as activate that control.
      if (e.target && e.target.closest && e.target.closest('input, select, textarea, button')) {
        return
      }

      if (this.key_locked) {
        return
      }
      this.key_locked = true
      this.key_timeout = setTimeout(() => { this.key_locked = false }, KEY_THROTTLE_MS)

      // Left and Right change pages. Up and Down are left to the browser's default
      // scrolling: the page is taller than the viewport, and intercepting them here would
      // double up with the native scroll. In continuous mode the observer records whichever
      // page is topmost, so scrolling inside a page does not change the saved page.
      const key = e.key.toLowerCase()
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
      }
    },
    // Continuous mode: reveal is not used for visibility here, so the page in view is
    // worked out from what is actually intersecting the viewport.
    start_scroll () {
      this.visible.clear()
      this.inview.clear()

      this.page_observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            this.visible.set(entry.target, entry.boundingClientRect.top)
            this.inview.add(Number(entry.target.dataset.page))
          } else {
            this.visible.delete(entry.target)
            this.inview.delete(Number(entry.target.dataset.page))
          }
        }

        if (this.visible.size === 0) {
          return
        }

        const top = [...this.visible.entries()].sort((a, b) => a[1] - b[1])[0][0]
        const page = Number(top.dataset.page)
        if (page && page !== this.current_page + 1) {
          this.current_page = page - 1
          this.queue_save(page - 1)
        }
      }, { threshold: 0 })

      this.growth_observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          this.extend_window()
        }
      }, { rootMargin: '1200px 0px' })

      this.observe_pages()
      if (this.$refs.sentinel) {
        this.growth_observer.observe(this.$refs.sentinel)
      }
      this.scroll_to_page(this.current_page + 1)
    },
    observe_pages () {
      this.$refs.slides.querySelectorAll('section[data-page]').forEach((section) => {
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
      this.inview.clear()

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
      this.paginate_page = new_page + 1
    }
  },
  mounted () {
    let comic_data_url = '/api/read/' + this.selector + '/'
    window.addEventListener('keydown', this.keyPress)
    api.get(comic_data_url)
    .then(response => {
      this.title = response.data.title
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
.navButtons {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 0;
    z-index: 1030;
  width: auto;
  cursor: pointer;
}
section {
  padding-bottom: 60px;
}

.shortcuts {
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

.shortcuts-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.shortcuts td {
  padding: 2px 8px 2px 0;
  vertical-align: top;
}

.shortcuts kbd {
  font-family: inherit;
  white-space: nowrap;
}

/* reveal.css is deliberately not loaded, so visibility is the `hidden` attribute and
   reveal's own transition classes do nothing. A transition cannot run across
   display:none -> block, so paged mode uses an animation on the slide that becomes
   present; continuous mode uses a transition driven by the IntersectionObserver. */
.reveal section.present img {
  animation: page-fade 0.3s ease;
}

.continuous img {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.continuous img.shown {
  opacity: 1;
}

@keyframes page-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .reveal section.present img,
  .continuous img {
    animation: none;
    transition: none;
  }
}
</style>
