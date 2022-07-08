<template>
  <the-navbar></the-navbar>
  <the-breadcrumbs></the-breadcrumbs>
  <comic-card></comic-card>
  <img alt="Vue logo" src="./assets/logo.png">
<!--  <HelloWorld msg="Welcome to Your Vue.js App"/>-->
</template>

<script>
// import HelloWorld from './components/HelloWorld.vue'

import '@coreui/vue';
import '@coreui/coreui/dist/css/coreui.min.css'
import TheNavbar from "@/components/TheNavbar";
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import ComicCard from "@/components/ComicCard";
export default {
  name: 'App',
  components: {
    ComicCard,
    TheBreadcrumbs,
    TheNavbar,
    // HelloWorld
  }
}
</script>

<style>

</style>
