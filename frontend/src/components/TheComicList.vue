<template>
  <the-breadcrumbs :crumbs="breadcrumbs"/>
  <CContainer>
    <CRow>
      <template v-for="comic in comics" :key="comic.title" >
        <comic-card :data="comic" />
      </template>
    </CRow>
  </CContainer>
</template>

<script>


import {CContainer, CRow} from "@coreui/vue"
import ComicCard from "@/components/ComicCard";
import api from '@/api'
import TheBreadcrumbs from "@/components/TheBreadcrumbs";

export default {
  name: "TheComicList",
  components: {TheBreadcrumbs, CRow, ComicCard, CContainer},
  data () {
    return {
      comics: [],
      breadcrumbs: [
        {id: 0, selector: '', name: 'Home'}
      ],
  }},
  props: {
    selector: String
  },
  methods: {
    updateBreadcrumbs () {
      if (this.selector) {
        let breadcrumb_url = this.$store.state.base_url + '/api/breadcrumbs/' + this.selector + '/'
        api.get(breadcrumb_url)
          .then(response => {
            this.breadcrumbs = response.data
          })
          .catch((error) => {console.log(error)})
      } else {
        this.breadcrumbs = [{id: 0, selector: '', name: 'Home'}]
      }
    },
    updateComicList () {
      let comic_list_url = this.$store.state.base_url + '/api/browse/'
      if (this.selector) {
        comic_list_url += this.selector
      }
      api.get(comic_list_url)
      .then(response => {
        this.comics = response.data
      })
      .catch((error) => {console.log(error)})
    },
  },
  mounted () {
    this.updateBreadcrumbs()
    this.updateComicList()
  },
  watch: {
    selector(oldSelector, newSelector) {
      this.updateBreadcrumbs()
      this.updateComicList()
    }
  }
}
</script>

<style scoped>

</style>