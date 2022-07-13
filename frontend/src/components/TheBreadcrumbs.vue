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
import api from "@/api";
export default {
  name: "TheBreadcrumbs",
  components: {
    CBreadcrumb,
    CBreadcrumbItem,
  },
  data () {
    return {
      crumbs: []
  }},
  props: {
    selector: String
  },
  methods: {
    updateBreadcrumbs () {
      if (this.selector) {
        let breadcrumb_url = this.$store.state.base_url + '/api/breadcrumbs/' + this.selector + '/'
        api.get(breadcrumb_url)
          .then(response => {
            this.crumbs = response.data
          })
          .catch((error) => {console.log(error)})
      } else {
        this.breadcrumbs = [{id: 0, selector: '', name: 'Home'}]
      }
    },
  },
  watch: {
    selector(oldSelector, newSelector) {
      this.updateBreadcrumbs()
    }
  },
  mounted () {
    this.updateBreadcrumbs()
  },
}
</script>

<style scoped>

</style>