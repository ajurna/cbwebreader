<template>
  <the-breadcrumbs :selector="selector" />
  <the-comic-reader :selector="selector" v-if="comic_loaded" :key="selector" />
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import TheComicReader from "@/components/TheComicReader";
import api from "@/api";
export default {
  name: "ReadView",
  components: {TheComicReader, TheBreadcrumbs},
  props: {
    selector: String
  },
  data () {
    return {
      comic_loaded: false,
    }
  },
  methods: {
    checkComicExists() {
      api.get('/api/read/' + this.selector + '/type/')
          .then(() => {
              this.comic_loaded = true
          })
          .catch((error) => {console.log(error)})
      }
  },
  mounted () {
    this.checkComicExists()
  }
}
</script>

<style scoped>

</style>
