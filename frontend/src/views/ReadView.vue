<template>
  <the-breadcrumbs :selector="selector" />
  <the-comic-reader :selector="selector" />
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import TheComicReader from "@/components/TheComicReader";
export default {
  name: "ReadView",
  components: {TheComicReader, TheBreadcrumbs},
  props: {
    selector: String
  }
}
</script>

<style scoped>

</style>