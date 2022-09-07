<template>
  <div class="container" ref="pdfContainer">
    <div class="row w-100 pb-5 mb-5" v-if="loaded">
      <pdf :src="pdfdata"  :page="page" ref="pdfWindow" :resize="true">
        <template v-slot:loading>
          loading content here...
        </template>
      </pdf>
    </div>
  </div>
  <div class="row navButtons pb-2">
    <comic-paginate
      v-model="page"
      :page_count="numPages"
      @setPage="setPage"
      @prevComic="prevComic"
      @nextComic="nextComic"
    />
  </div>
</template>

<script>
import pdfvuer from 'pdfvuer'
import api from "@/api";
import * as Hammer from 'hammerjs'
import ComicPaginate from "@/components/ComicPaginate";

export default {
  name: "ThePdfReader",
  components: {
    ComicPaginate,
    pdf: pdfvuer
  },
  data () {
    return {
      page: 1,
      numPages: 0,
      pdfdata: undefined,
      errors: [],
      scale: 'page-width',
      loaded: false,
      key_timeout: null,
      hammertime: null,
      next_comic: {},
      prev_comic: {}
    }
  },
  props: {
    selector: String
  },
  computed: {
  },
  mounted () {
    this.getPdf()
    window.addEventListener('keyup', this.keyPressDebounce)
  },
  beforeUnmount() {
    window.removeEventListener('keyup', this.keyPressDebounce)
  },
  watch: {
  },
  methods: {
    getPdf () {
      let comic_data_url = '/api/read/' + this.selector + '/'
      api.get(comic_data_url)
        .then(response => {
          let parameter = {
            url: '/api/read/' + this.selector + '/pdf/',
            httpHeaders: { Authorization: 'Bearer ' + this.$store.state.jwt.access },
            withCredentials: true,
          }
          this.pdfdata = pdfvuer.createLoadingTask(parameter);
          this.pdfdata.then(pdf => {
            this.numPages = pdf.numPages;
            this.loaded = true
            this.page = response.data.last_read_page+1
            this.setReadPage(this.page)
            this.next_comic = response.data.next_comic
            this.prev_comic = response.data.prev_comic
            this.hammertime = new Hammer(this.$refs.pdfContainer, {})
            this.hammertime.on('swipeleft', (_e, self=this) => {
              self.nextPage()
            })
            this.hammertime.on('swiperight', (_e, self=this) => {
              self.prevPage()
            })
            this.hammertime.on('tap', (_e, self=this) => {
              self.nextPage()
            })
          }).catch(e => {console.log(e)});
      })

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
    nextPage () {
      if (this.page < this.numPages){
        this.page += 1
        this.setReadPage(this.page)
      } else {
        this.nextComic()
      }
    },
    prevPage() {
      if (this.page > 1){
        this.page -= 1
        this.setReadPage(this.page)
      } else {
        this.prevComic()
      }
    },
    setPage(num) {
      this.page = num
      this.setReadPage(this.page)
    },
    setReadPage(num){
      this.$refs.pdfContainer.scrollIntoView()
      let payload = {
          page: num-1
      }
      api.put('/api/read/'+ this.selector +'/set_page/', payload)
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
</style>
