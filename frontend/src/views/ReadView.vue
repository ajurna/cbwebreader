<template>
  <the-breadcrumbs :selector="selector" />
  <the-comic-reader :comic_data="comic_data" v-if="comic_loaded" />
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
      comic_data: {},
      comic_loaded: false
    }
  },
  mounted () {
    let comic_data_url = this.$store.state.base_url + '/api/read/' + this.selector + '/'
    api.get(comic_data_url)
        .then(response => {
          this.comic_data = response.data
          this.comic_loaded = true
        })
        .catch((error) => {console.log(error)})
  }
}
</script>

<style scoped>

</style>