<template>
  <the-breadcrumbs :selector="selector" />
  <the-comic-reader :selector="selector" v-if="comic_loaded" :key="selector" />
  <the-pdf-reader :selector="selector" v-if="pdf_loaded" :key="selector" />
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
  methods: {
    updateType() {
      let comic_data_url = '/api/read/' + this.selector + '/type/'
      api.get(comic_data_url)
          .then(response => {
            console.log('resp')
            if (response.data.type === 'pdf'){
              this.pdf_loaded = true
              this.comic_loaded = false
            } else {
              this.comic_loaded = true
              this.pdf_loaded = false
            }
          })
          .catch((error) => {console.log(error)})
      }
  },
  mounted () {
    this.updateType()
  },
  beforeUpdate() {
    this.updateType()
  }
}
</script>

<style scoped>

</style>