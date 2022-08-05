<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs" />
  <CContainer>
    <user-list />
  </CContainer>
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import UserList from "@/components/UserList";
import {CContainer} from "@coreui/vue";
export default {
  name: "UserView",
  components: {UserList, TheBreadcrumbs, CContainer},
  props: {
    userid: Number
  },
  data () {
    return {
      crumbs: [
          {id: 0, selector: '', name: 'Home'},
          {id: 1, selector: '', name: 'Users'}
      ]
  }},
}
</script>

<style scoped>

</style>