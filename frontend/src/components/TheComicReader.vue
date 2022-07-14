<template>
  <div class="reveal" id="comic_box" ref="comic_box">
    <div id="slides_div" class="slides">
      <section v-for="(page, index) in comic_data.pages" :key="page.index" :data-menu-title="page.page_file_name">
        <img :data-src="'/image/' + comic_data.selector + '/' + page.index " class="w-100"  :alt="page.page_file_name">
      </section>
    </div>
  </div>
</template>

<script>

import Reveal from "reveal.js";

export default {
  name: "TheComicReader",
  data () {
    return {
    }
  },
  props: {
    comic_data: Object
  },
  methods: {
  },
  watch: {
    '$route' (to, from) {
      // Reveal.initialize()
    }
  },
  mounted () {
    // Reveal.initialize()
  },
}
</script>
<script setup>
    import {onBeforeRouteUpdate} from "vue-router";
    import {onUpdated, onMounted, onActivated, onUnmounted, ref } from "vue"
    // import Reveal from "reveal.js";
    const comic_box = ref('comic_box')
    onBeforeRouteUpdate(async (to, from) => {
      // only fetch the user if the id changed as maybe only the query or the hash changed
      console.log(to)
      console.log(from)
    })
    onUpdated(async () => {
      console.log('onUpdated')
    })
    onMounted(async () => {
      console.log('onMounted')
      Reveal(comic_box.value).initialize()
      console.log(comic_box.value)
      console.log(Reveal.getRevealElement())
      console.log(Reveal.getSlidesElement())
      console.log(Reveal.getViewportElement())
    })
    onUnmounted(async () => {
      console.log('onUnmounted')
      Reveal.destroy()
      console.log(Reveal.getRevealElement())
      console.log(Reveal.getSlidesElement())
      console.log(Reveal.getViewportElement())
    })
    onActivated(async () => {
      console.log('onActivated')
      // Reveal.sync()
    })
</script>


<style scoped>

</style>