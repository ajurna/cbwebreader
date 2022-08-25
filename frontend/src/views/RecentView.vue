<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs" />
  <the-recent-table />
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import TheRecentTable from "@/components/TheRecentTable";
export default {
  name: "RecentView",
  components: {TheRecentTable, TheBreadcrumbs},
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