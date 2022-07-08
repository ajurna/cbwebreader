<template>
    <CBreadcrumb>
      <template v-for="(item, index) in crumbs" :key="item.id">
        <CBreadcrumbItem href="#" v-if="index !== crumbs.length - 1">{{ item.text }}</CBreadcrumbItem>
        <CBreadcrumbItem v-else active>{{ item.text }}</CBreadcrumbItem>
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
      crumbs: [
      {id: 0, href: '/home', text:'home'},
      {id: 1, href: '/library', text:'Library'},
      {id: 2, href: '/data', text:'Data'}
    ]
  }},
  props: {

  }
}
</script>

<style scoped>

</style>