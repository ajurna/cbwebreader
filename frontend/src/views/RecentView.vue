<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs"></the-breadcrumbs>
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
export default {
  name: "RecentView",
  components: {TheBreadcrumbs},
  data () {
    return {
      crumbs: [
          {id: 0, selector: '', name: 'Home'},
          {id: 1, selector: '', name: 'Recent'}
      ]
  }},
}
</script>

<style scoped>

</style>