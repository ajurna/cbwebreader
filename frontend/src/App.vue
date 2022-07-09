<template>
  <the-navbar />
  <the-breadcrumbs />
  <router-view/>
</template>

<style>
</style>
<script>
import TheNavbar from "@/components/TheNavbar";
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
export default {
  components: {TheBreadcrumbs, TheNavbar}
}
</script>