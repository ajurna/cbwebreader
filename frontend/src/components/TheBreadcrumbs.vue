<template>
  <nav aria-label="breadcrumb" class="px-5">
    <ol class="breadcrumb " >
      <template v-for="(item, index) in crumbs" :key="item.id">
        <template v-if="index !== crumbs.length - 1">
          <li class="breadcrumb-item" v-if="item.selector">
            <router-link :to="{'name': 'browse', params: { selector: item.selector }}">{{ item.name }}</router-link>
          </li>
          <li class="breadcrumb-item" v-else-if="item.route">
            <router-link :to="item.route">{{ item.name }}</router-link>
          </li>
          <li class="breadcrumb-item" v-else>
            <router-link :to="{'name': 'browse'}">{{ item.name }}</router-link>
          </li>
        </template>
        <li class="breadcrumb-item active" aria-current="page" v-else>{{ item.name }}</li>
      </template>
    </ol>
  </nav>

</template>

<script>
import api from "@/api";
export default {
  name: "TheBreadcrumbs",
  components: { },
  data () {
    return {
      crumbs: []
  }},
  props: {
    selector: String,
    manual_crumbs: Object
  },
  methods: {
    updateBreadcrumbs () {
      if (this.selector) {
        let breadcrumb_url = '/api/browse/' + this.selector + '/breadcrumbs/'
        api.get(breadcrumb_url)
            .then(response => {
              this.crumbs = response.data
            })
            .catch((error) => {
              console.log(error)
            })
      }else if (this.manual_crumbs){
        this.crumbs = this.manual_crumbs
      } else {
        this.crumbs = [{id: 0, selector: '', name: 'Home'}]
      }
    },
  },
  watch: {
    selector() {
      this.updateBreadcrumbs()
    },
    manual_crumbs () {
      this.updateBreadcrumbs()
    }
  },
  mounted () {
    this.updateBreadcrumbs()
  },
}
</script>

<style scoped>
.breadcrumb-item a {
  text-decoration: none;
}
nav {
  background: lightgrey;
}
</style>
