<template>
  <div class="reveal" id="comic_box" ref="comic_box" >
    <div id="slides_div" class="slides"  ref="slides">
      <section v-for="(page, index) in comic_data.pages" :key="page.index" :data-menu-title="page.page_file_name" hidden>
        <img :data-src="'/api/read/' + comic_data.selector + '/image/' + page.index + '/'" class="w-100"  :alt="page.page_file_name">
      </section>
    </div>
  </div>
  <paginate
    v-model="this.paginate_page"
    :page-count="this.comic_data.pages.length"
    :click-handler="this.setPage"
    :prev-text="'Prev'"
    :next-text="'Next'"
    :container-class="'pagination'"
  >
  </paginate>
</template>

<script>
import Reveal from "reveal.js";
import api from "@/api";
import 'reveal.js-menu/menu.css'
import {CPagination, CPaginationItem} from "@coreui/vue";
import Paginate from "vuejs-paginate-next";




export default {
  name: "TheComicReader",
  components: {CPagination, CPaginationItem, Paginate},
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
        // if (nav.prev_type === 'ComicBook'){
        //     window.location = "/comic/read/"+ nav.prev_path +"/"
        // } else {
        //     window.location = "/comic/"+ nav.prev_path +"/"
        // }
      } else {
        this.current_page -= 1
        this.deck.slide(this.current_page)
      }
    },
    nextPage(){
      if (this.deck.isLastSlide()){
        // if (nav.next_type === 'ComicBook'){
        //     window.location = "/comic/read/"+ nav.next_path +"/"
        // } else {
        //     window.location = "/comic/"+ nav.next_path +"/"
        // }
      } else {
        this.current_page += 1
        this.deck.slide(this.current_page)
      }
    },
    setPage(pageNum){
      console.log(pageNum)
      this.current_page = pageNum-1
      this.deck.slide(this.current_page)
    }
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
  },
}
</script>


<style scoped>
.pagination {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 0;
    z-index: 1030;
  cursor: pointer;
}
</style>