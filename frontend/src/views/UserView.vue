<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs" />
  <CContainer>
    <messages :messages="messages" />
    <user-list :users="users" v-if="!userid"/>
    <user-edit v-if="user_data" :user="user_data" :messages="messages"/>
  </CContainer>
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import UserList from "@/components/UserList";
import api from "@/api";
import UserEdit from "@/components/UserEdit";
import Messages from "@/components/Messages";

const default_crumbs = [
  {id: 0, selector: '', name: 'Home'},
  {id: 1, route: {'name': 'user'}, name: 'Users'}
]
export default {
  name: "UserView",
  components: {Messages, UserEdit, UserList, TheBreadcrumbs},
  props: {
    userid: String
  },
  data () {
    return {
      crumbs: [...default_crumbs],
      users: [],
      viewUserList: true,
      user_data: null,
      messages: []
  }},
  methods: {
    updateUsers() {
      api.get('/api/users/').then(response => {
        this.users = response.data
      })
    },
    getUser() {
      api.get('/api/users/' + this.userid + '/').then(response => {
        this.user_data = response.data
        this.crumbs.push({id: 1, selector: '', name: response.data.username})
      })
    }
  },
  mounted() {
    this.updateUsers()
    if (this.userid){
      this.getUser()
    }
  },
  beforeUpdate() {
    this.crumbs = [...default_crumbs]
    if (this.userid){
      this.getUser()
    } else {
      this.user_data = null
      this.crumbs = default_crumbs
    }
  }
}
</script>

<style scoped>

</style>