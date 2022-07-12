<template>
  <CContainer>
    <CRow v-if="viewable">
      <template v-for="comic in comics" :key="comic.title" >
        <comic-card :data="comic" />
      </template>
    </CRow>
  </CContainer>
</template>

<script>


import {CContainer, CRow} from "@coreui/vue"
import ComicCard from "@/components/ComicCard";
// import axios from 'axios'
// import router from "@/router";
import api from '@/api'

export default {
  name: "TheComicList",
  components: {CRow, ComicCard, CContainer},
  data () {
    return {
      comics: [],
      viewable: true
  }},
  async mounted () {
    console.log()
    api.get('https://localhost:8000/api/browse/')
      .then(response => {
        this.comics = response.data
      })
        .catch((error) => {console.log(error)})

  }
}
</script>

<style scoped>

</style>