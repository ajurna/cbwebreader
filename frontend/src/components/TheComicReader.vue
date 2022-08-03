<template>
  <div class="reveal" id="comic_box" ref="comic_box" >
    <div id="slides_div" class="slides"  ref="slides">
      <section class="" v-for="(page, index) in comic_data.pages" :key="page.index" :data-menu-title="page.page_file_name" hidden>
        <img :data-src="'/api/read/' + comic_data.selector + '/image/' + page.index + '/'" class="w-100"  :alt="page.page_file_name">
      </section>
    </div>
  </div>
  <CRow class="navButtons pb-2">
    <CListGroup :layout="'horizontal'">
      <CListGroupItem class="p-1 pt-2 page-link pl-2 pr-2" @click="prevComic">Prev&nbsp;Comic</CListGroupItem>
      <paginate
        v-model="this.paginate_page"
        :page-count="this.comic_data.pages.length"
        :click-handler="this.setPage"
        :prev-text="'Prev'"
        :next-text="'Next'"
        :container-class="'pagination'"
      >
      </paginate>
      <CListGroupItem  class="p-1 pt-2 page-link pl-2 pr-2">Next&nbsp;Comic</CListGroupItem>
    </CListGroup>
  </CRow>

</template>

<script>
import Reveal from "reveal.js";
import api from "@/api";
import 'reveal.js-menu/menu.css'
import {CPagination, CPaginationItem, CRow, CButton, CCol, CListGroup, CListGroupItem} from "@coreui/vue";
import Paginate from "vuejs-paginate-next";
import * as Hammer from 'hammerjs'

export default {
  name: "TheComicReader",
  components: {CPagination, CPaginationItem, Paginate, CRow, CButton, CCol, CListGroup, CListGroupItem},
  data () {
    return {
      current_page: 0,
      paginate_page: 1,
      deck: null
    }
  },
  props: {
    comic_data: Object
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
        name: this.comic_data.prev_comic.route,
        params: {selector: this.comic_data.prev_comic.selector}
      })
    },
    nextComic(){
      this.$router.push({
        name: this.comic_data.next_comic.route,
        params: {selector: this.comic_data.next_comic.selector}
      })
    },
    nextPage(){
      if (this.deck.isLastSlide()){
        this.$router.push({
          name: this.comic_data.next_comic.route,
          params: {selector: this.comic_data.next_comic.selector}
        })
      } else {
        this.current_page += 1
        this.deck.slide(this.current_page)
      }
    },
    setPage(pageNum){
      this.current_page = pageNum-1
      this.deck.slide(this.current_page)
    },
  },
  watch: {
    'current_page' (new_page) {
      this.paginate_page = new_page + 1
    }
  },
  mounted () {
    const set_read_url = this.$store.state.base_url + '/api/set_read/' + this.comic_data.selector + '/'
    this.current_page = this.comic_data.last_read_page
    this.paginate_page = this.current_page + 1
    this.deck = Reveal(this.$refs.comic_box)
    this.deck.initialize({
      controls: false,
      width: "100%",
      height: "100%",
      margin: 0,
      minScale: 1,
      maxScale: 1,
      keyboard: {
          37: () => {this.prevPage()},
          39: () => {this.nextPage()},
          38: () => {window.scrollTo({ top: window.scrollY-window.innerHeight*.6, left: 0, behavior: 'smooth' })},
          40: () => {window.scrollTo({ top: window.scrollY+window.innerHeight*.6, left: 0, behavior: 'smooth' })},
        },
      touch: false,
      transition: 'slide',
      plugins: [  ]
    }).then(() => {
      this.deck.slide(this.current_page)
      this.deck.on( 'slidechanged', () => {
        this.$refs.comic_box.scrollIntoView({behavior: 'smooth'})
        api.put(set_read_url, {page: event.indexh})
      });
    })

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