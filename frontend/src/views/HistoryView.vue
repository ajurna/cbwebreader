<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs" />
  <history-table />
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import HistoryTable from "@/components/HistoryTable";
export default {
  name: "HistoryView",
  components: {HistoryTable, TheBreadcrumbs},
  data () {
    return {
      crumbs: [
          {id: 0, selector: '', name: 'Home'},
          {id: 1, selector: '', name: 'History'}
      ]
  }},
}
</script>

<style scoped>

</style>
