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
      comic_data: {},
      comic_loaded: false,
    }
  },
  methods: {
    updateType() {
      let comic_data_url = '/api/read/' + this.selector + '/type/'
      api.get(comic_data_url)
          .then(response => {
              this.comic_loaded = true
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
