<template>
  <div class="reveal" id="comic_box" ref="comic_box" >
    <div id="slides_div" class="slides"  ref="slides">
      <section class="" v-for="page in pages" :key="page.index" :data-menu-title="page.page_file_name" hidden>
        <img :data-src="'/api/read/' + selector + '/image/' + page.index + '/'" class="w-100"  :alt="page.page_file_name">
      </section>
    </div>
  </div>
  <CRow class="navButtons pb-2">
    <CListGroup :layout="'horizontal'">
      <CListGroupItem class="p-1 pt-2 page-link pl-2 pr-2" @click="prevComic">Prev&nbsp;Comic</CListGroupItem>
      <paginate
        v-model="paginate_page"
        :page-count="pages.length"
        :click-handler="this.setPage"
        :prev-text="'Prev'"
        :next-text="'Next'"
        :container-class="'pagination'"
      >
      </paginate>
      <CListGroupItem  class="p-1 pt-2 page-link pl-2 pr-2" @click="nextComic">Next&nbsp;Comic</CListGroupItem>
    </CListGroup>
  </CRow>

</template>

<script>
import Reveal from "reveal.js";
import api from "@/api";
import 'reveal.js-menu/menu.css'
import Paginate from "vuejs-paginate-next";
import * as Hammer from 'hammerjs'

export default {
  name: "TheComicReader",
  components: {Paginate},
  data () {
    return {
      current_page: 0,
      paginate_page: 1,
      deck: null,
      title: '',
      prev_comic: {},
      next_comic: {},
      pages: [],
    }
  },
  props: {
    selector: String
  },
  methods: {
    prevPage(){
      if (this.deck.isFirstSlide()){
        this.prevComic()
      } else {
        this.current_page -= 1
        this.deck.slide(this.current_page)
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
    nextPage(){
      if (this.deck.isLastSlide()){
        this.nextComic()
      } else {
        this.current_page += 1
        this.deck.slide(this.current_page)
      }
    },
    setPage(pageNum){
      this.current_page = pageNum-1
      this.deck.slide(this.current_page)
    },
    keyPressDebounce(e){
      clearTimeout(this.key_timeout)
      this.key_timeout = setTimeout(() => {this.keyPress(e)}, 50)
    },
    keyPress(e) {
      if (e.key === 'ArrowRight') {
        this.nextPage()
      } else if (e.key === 'ArrowLeft') {
        this.prevPage()
      } else if (e.key === 'ArrowUp') {
        window.scrollTo({
          top: window.scrollY-window.innerHeight*.7,
          left: 0,
          behavior: 'smooth'
        });
      } else if (e.key === 'ArrowDown') {
        window.scrollTo({
          top: window.scrollY+window.innerHeight*.7,
          left: 0,
          behavior: 'smooth'
        });
      }
    }
  },
  watch: {
    'current_page' (new_page) {
      this.paginate_page = new_page + 1
    }
  },
  mounted () {
    const set_read_url = this.$store.state.base_url + '/api/read/' + this.selector + '/set_page/'
    let comic_data_url = '/api/read/' + this.selector + '/'
    window.addEventListener('keyup', this.keyPressDebounce)
    api.get(comic_data_url)
    .then(response => {
      this.title = response.data.title
      this.current_page = response.data.last_read_page
      this.prev_comic = response.data.prev_comic
      this.next_comic = response.data.next_comic
      this.pages = response.data.pages

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
        this.deck.on( 'slidechanged', () => {
          this.$refs.comic_box.scrollIntoView({behavior: 'smooth'})
          api.put(set_read_url, {page: event.indexh})
        });
      })

      this.hammertime = new Hammer(this.$refs.comic_box.$el, {})
      this.hammertime.on('swipeleft', (_e, self=this) => {
        self.nextPage()
      })
      this.hammertime.on('swiperight', (_e, self=this) => {
        self.prevPage()
      })
      this.hammertime.on('tap', (_e, self=this) => {
        self.nextPage()
      })

    })
    .catch((error) => {console.log(error)})
  },
  beforeUnmount() {
    window.removeEventListener('keyup', this.keyPressDebounce)
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
.list-group-item {
  /*padding: 0;*/
}
</style>