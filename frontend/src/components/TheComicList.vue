<template>
  <CContainer>
    <CRow>
      <template v-for="comic in comics" :key="comic.title">
        <comic-card :data="comic" />
      </template>
    </CRow>
  </CContainer>
</template>

<script>


import {CContainer, CRow} from "@coreui/vue"
import ComicCard from "@/components/ComicCard";
import axios from 'axios'
import router from "@/router";

export default {
  name: "TheComicList",
  components: {CRow, ComicCard, CContainer},
  data () {
    return {
      comics: []
  }},
  mounted () {
    console.log()
    axios
      .get('https://localhost:8000/api/browse/',
          {
            headers: {
              Authorization: "Bearer " + this.$store.state.jwt.access
            }})
      .then(response => (this.comics = response.data))
        .catch(() => {
          this.$store.dispatch('refreshToken')
          router.push('/')
        })

  }
}
</script>

<style scoped>

</style>