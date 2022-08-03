<template>
  <the-breadcrumbs :selector="selector" />
  <the-comic-reader :comic_data="comic_data" v-if="comic_loaded" />
  <the-pdf-reader :comic_data="comic_data" v-if="pdf_loaded"/>
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import TheComicReader from "@/components/TheComicReader";
import api from "@/api";
import ThePdfReader from "@/components/ThePdfReader";
export default {
  name: "ReadView",
  components: {ThePdfReader, TheComicReader, TheBreadcrumbs},
  props: {
    selector: String
  },
  data () {
    return {
      comic_data: {},
      comic_loaded: false,
      pdf_loaded: false
    }
  },
  mounted () {
    let comic_data_url = '/api/read/' + this.selector + '/'
    api.get(comic_data_url)
        .then(response => {
          this.comic_data = response.data
          if (this.comic_data.title.toLowerCase().endsWith('.pdf')){
            this.pdf_loaded = true
          } else {
            this.comic_loaded = true
          }
        })
        .catch((error) => {console.log(error)})
  }
}
</script>

<style scoped>

</style>