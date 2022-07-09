<template>
  <the-comic-list />
</template>

<script>
// @ is an alias to /src
// import HelloWorld from '@/components/HelloWorld.vue'
import TheComicList from "@/components/TheComicList";

export default {
  name: 'HomeView',
  components: {
    TheComicList,
    // HelloWorld
  }
}
</script>
