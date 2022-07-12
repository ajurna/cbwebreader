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

export default {
  name: "TheComicList",
  components: {CRow, ComicCard, CContainer},
  data () {
    return {
      comics: [],
  }},
  props: {
    selector: String
  },
  mounted () {
    let url = 'https://localhost:8000/api/browse/'
    if (this.selector) {
      url += this.selector
    }
    api.get(url)
      .then(response => {
        this.comics = response.data
      })
        .catch((error) => {console.log(error)})

  }
}
</script>

<style scoped>

</style>