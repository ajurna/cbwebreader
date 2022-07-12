<template>
    <CBreadcrumb>
      <template v-for="(item, index) in crumbs" :key="item.id">
        <CBreadcrumbItem :href="(item.selector ? '/browse/' + item.selector + '/': '/')" v-if="index !== crumbs.length - 1">{{ item.name }}</CBreadcrumbItem>
        <CBreadcrumbItem v-else active>{{ item.name }}</CBreadcrumbItem>
      </template>
    </CBreadcrumb>

</template>

<script>
import { CBreadcrumbItem, CBreadcrumb } from '@coreui/vue'
export default {
  name: "TheBreadcrumbs",
  components: {
    CBreadcrumb,
    CBreadcrumbItem,
  },
  data () {
    return {

  }},
  props: {
    crumbs: Object
  }
}
</script>

<style scoped>

</style>