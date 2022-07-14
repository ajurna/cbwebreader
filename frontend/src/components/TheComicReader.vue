<template>
  <div class="reveal" id="comic_box" ref="comic_box">
    <div id="slides_div" class="slides">
      <section v-for="(page, index) in comic_data.pages" :key="page.index" :data-menu-title="page.page_file_name">
        <img :data-src="'/image/' + comic_data.selector + '/' + page.index " class="w-100"  :alt="page.page_file_name">
      </section>
    </div>
  </div>
</template>

<script>
import Reveal from "reveal.js";
import api from "@/api";

export default {
  name: "TheComicReader",
  data () {
    return {
      current_page: 0,
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
  },
  watch: {
    '$route' (to, from) {
      // Reveal.initialize()
    }
  },
  mounted () {
    const set_read_url = this.$store.state.base_url + '/api/set_read/' + this.comic_data.selector + '/'
    this.current_page = this.comic_data.last_read_page
    this.deck = Reveal(this.$refs.comic_box)
    this.deck.initialize({
      controls: false,
      width: "100%",
      height: "100%",
      margin: 0,
      minScale: 1,
      maxScale: 1,
      disableLayout: true,
      progress: true,
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
        setTimeout(event =>{document.getElementsByClassName('slides')[0].scrollIntoView({behavior: 'smooth'})}, 100)
        // $.ajax({url: "/comic/set_page/" + nav.cur_path + "/" + event.indexh + "/"})
        api.put(set_read_url, {page: event.indexh})
});
    })
  },
}
</script>


<style scoped>

</style>