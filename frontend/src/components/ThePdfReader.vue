<template>
  <CContainer ref="pdfContainer">
    <CRow class="w-100 pb-5 mb-5" v-if="loaded" >
        <pdf :src="pdfdata"  :page="page" ref="pdfWindow" :resize="true">
          <template slot="loading">
            loading content here...
          </template>
        </pdf>
    </CRow>
  </CContainer>
  <CRow class="navButtons pb-2">
    <CListGroup :layout="'horizontal'">
      <CListGroupItem class="p-1 pt-2 page-link pl-2 pr-2" @click="prevComic">Prev&nbsp;Comic</CListGroupItem>
      <paginate
        v-model="page"
        :page-count="numPages"
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
import {CContainer, CRow, CButtonGroup, CButton, CListGroup, CListGroupItem} from "@coreui/vue";
import pdfvuer from 'pdfvuer'
import api from "@/api";
import Paginate from "vuejs-paginate-next";
import * as Hammer from 'hammerjs'


export default {
  name: "ThePdfReader",
  components: {
    CContainer, CRow, CButtonGroup, CButton, pdf: pdfvuer, Paginate, CListGroup, CListGroupItem
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
      hammertime: null
    }
  },
  props: {
    comic_data: Object
  },
  computed: {
  },
  mounted () {
    this.getPdf()
    window.addEventListener('keyup', this.keyPressDebounce)
  },
  unmounted() {
    window.removeEventListener('keyup', this.keyPressDebounce)
  },
  watch: {
  },
  methods: {
    getPdf () {
      this.pdfdata = pdfvuer.createLoadingTask('/api/read/' + this.comic_data.selector + '/pdf/');
      this.pdfdata.then(pdf => {
        this.numPages = pdf.numPages;
        this.loaded = true
        this.page = this.comic_data.last_read_page

        this.hammertime = new Hammer(this.$refs.pdfContainer.$el, {})
        this.hammertime.on('swipeleft', (_e, self=this) => {
          self.nextPage()
        })
        this.hammertime.on('swiperight', (_e, self=this) => {
          self.prevPage()
        })
        this.hammertime.on('tap', (_e, self=this) => {
          self.nextPage()
        })
      });
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
    nextPage () {
      if (this.page < this.numPages){
        this.page += 1
        this.setReadPage(this.page)
      }
    },
    prevPage() {
      if (this.page > 1){
        this.page -= 1
        this.setReadPage(this.page)
      }
    },
    setPage(num) {
      this.page = num
      this.setReadPage(this.page)
    },
    setReadPage(num){
      this.$refs.pdfWindow.$el.scrollIntoView()
      let payload = {
          page: num
      }
      api.put('/api/set_read/'+ this.comic_data.selector +'/', payload)
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