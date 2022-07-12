<template>
  <the-navbar />
  <router-view/>
</template>

<style>
</style>
<script>
import TheNavbar from "@/components/TheNavbar.vue";
export default {
  components: {TheNavbar}
}
</script>