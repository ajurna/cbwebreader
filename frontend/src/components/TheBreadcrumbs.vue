<template>
    <CBreadcrumb>
      <template v-for="(item, index) in crumbs" :key="item.id">
        <CBreadcrumbItem v-if="index !== crumbs.length - 1">
          <router-link :to="(item.selector ? {'name': 'browse', params: { selector: item.selector }} : {'name': 'home'})">{{ item.name }}</router-link>
        </CBreadcrumbItem>
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