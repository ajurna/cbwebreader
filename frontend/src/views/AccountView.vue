<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs" />
  <the-account-form />
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import TheAccountForm from "@/components/TheAccountForm";
export default {
  name: "AccountView",
  components: {TheAccountForm, TheBreadcrumbs},
  data () {
    return {
      crumbs: [
          {id: 0, selector: '', name: 'Home'},
          {id: 1, selector: '', name: 'Account'}
      ]
  }},
}
</script>

<style scoped>

</style>