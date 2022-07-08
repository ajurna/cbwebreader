<template>
  <the-navbar></the-navbar>
  <the-breadcrumbs></the-breadcrumbs>
  <the-comic-list></the-comic-list>
</template>

<script>

import '@coreui/vue';
import '@coreui/coreui/dist/css/coreui.min.css'
import TheNavbar from "@/components/TheNavbar";
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import TheComicList from "@/components/TheComicList";

export default {
  name: 'App',
  components: {
    TheComicList,
    TheBreadcrumbs,
    TheNavbar,
  }
}
</script>

<style>

</style>
