<template>
  <the-breadcrumbs :manual_crumbs="this.crumbs" />
  <div class="container">
    <alert-messages :messages="messages" @removeMessage="removeMessage" />
    <user-list :users="users" v-if="!userid"/>
    <user-edit v-if="user_data" :user="user_data" @add-message="addMessage"/>
    <add-user v-if="!userid" @user-added="updateUsers" @add-message="addMessage"/>
  </div>
</template>

<script>
import TheBreadcrumbs from "@/components/TheBreadcrumbs";
import UserList from "@/components/UserList";
import api from "@/api";
import UserEdit from "@/components/UserEdit";
import alertMessages from "@/components/AlertMessages";
import AddUser from "@/components/AddUser";
import router from "@/router";

const default_crumbs = [
  {id: 0, selector: '', name: 'Home'},
  {id: 1, route: {'name': 'user'}, name: 'Users'}
]
export default {
  name: "UserView",
  components: {AddUser, alertMessages, UserEdit, UserList, TheBreadcrumbs},
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
    removeMessage(item) {
      this.messages.pop(this.messages.indexOf(item))
    },
    updateUsers() {
      api.get('/api/users/').then(response => {
        this.users = response.data
      })
    },
    getUser() {
      api.get('/api/users/' + this.userid + '/').then(response => {
        this.user_data = response.data
        this.crumbs.push({id: 1, selector: '', name: response.data.username})
      }).catch(() => {
        this.messages.push({
          color: 'danger',
          text: 'User with id "' + this.userid + '" does not exist.'
        })
        router.push({name: 'user'})
      })
    },
    addMessage(message){
      this.messages.push(message)
    }
  },
  mounted() {
    this.updateUsers()
    if (this.userid){
      this.getUser()
    }
  },
  watch: {
    $route(to, from) {
      this.updateUsers()
      this.crumbs = [...default_crumbs]
      if (this.userid){
        this.getUser()
      } else {
        this.user_data = null
        this.crumbs = default_crumbs
      }
    }
  },
}
</script>

<style scoped>

</style>
