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


export default {
  name: "TheComicList",
  components: {CRow, ComicCard, CContainer},
  data () {
    return {
      comics: [
      {
        title: '100 Bullets (1997)',
        url: '/comic/hBIlAchXRxaXs9ZCXaDWLg/',
        thumbnail: 'logo.png',
        progress: 50,
        total: 100
      },
      {
        title: '100 Bullets (1998)',
        url: '/comic/hBIlAchXRxaXs9ZCXaDWLg/',
        thumbnail: 'logo.png',
        progress: 50,
        total: 100
      },
      {
        title: '100 Bullets (1999)',
        url: '/comic/hBIlAchXRxaXs9ZCXaDWLg/',
        thumbnail: 'logo.png',
        progress: 50,
        total: 100
      }
    ]
  }},
}
</script>

<style scoped>

</style>