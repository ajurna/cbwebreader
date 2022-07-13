<template>
  <div class="reveal" id="comic_box">
    <div id="slides_div" class="slides">
      <section v-for="(item, index) in data.pages" :key="item.index" :data-menu-title="item.page_file_name">
        <img :data-src="'/image/' + selector + '/' + item.index " class="w-100"  :alt="item.page_file_name">
      </section>
    </div>
  </div>
</template>

<script>
import Reveal from 'reveal.js';

import api from "@/api";


export default {
  name: "TheComicReader",
  data () {
    return {
      data: []
    }
  },
  props: {
    selector: String
  },
  methods: {
    makeReadable(){
      console.log('started')
      let comic_data_url = this.$store.state.base_url + '/api/read/' + this.selector + '/'
      api.get(comic_data_url)
        .then(response => {
          this.data = response.data
          console.log(response.data)
          Reveal.initialize({
            controls: true,
            width: "100%",
            height: "100%",
            margin: 0,
            minScale: 1,
            maxScale: 1,
            disableLayout: true,
            progress: true,
            keyboard: {
                37: () => {prevPage()},
                39: () => {nextPage()},
                38: () => {window.scrollTo({ top: window.scrollY-window.innerHeight*.6, left: 0, behavior: 'smooth' })},
                40: () => {window.scrollTo({ top: window.scrollY+window.innerHeight*.6, left: 0, behavior: 'smooth' })},
              },
            touch: false,
            transition: 'slide',
            plugins: [  ]
            }).then(() => {
                Reveal.sync();
                Reveal.slide(0)
            });
        })
        .catch((error) => {console.log(error)})
    },
  },
  // watch: {
  //   selector(old, n) {
  //     console.log('watcher')
  //     this.makeReadable()
  //   }
  // },
  mounted () {
    this.makeReadable()

  },
  beforeUnmount() {
    Reveal.destroy();
  }
}
</script>

<style scoped>

</style>