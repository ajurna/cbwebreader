<template>
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
    this.updateComicList()
  },
  watch: {
    selector(oldSelector, newSelector) {
      this.updateComicList()
    }
  }
}
</script>

<style scoped>

</style>