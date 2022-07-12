<template>
  <the-navbar />
  <router-view/>
</template>

<style>
</style>
<script>
import TheNavbar from "@/components/TheNavbar";
export default {
  components: {TheNavbar}
}
</script>