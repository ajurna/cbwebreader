<template>
  <h1>Create your admin account.</h1>
  <form @submit="saveForm">
    <label class="form-label">Username</label>
    <input class="form-control" type="text" v-model="username">

    <label class="form-label">Email address</label>
    <input class="form-control" type="email" v-model="email">

    <label class="form-label">Password</label>
    <input class="form-control" type="password" v-model="password">

    <label class="form-label">Confirm Password</label>
    <input class="form-control" type="password" v-model="confirm_password">

    <button class="btn btn-primary mr-5 mt-2" type="submit">Save</button>
  </form>
</template>

<script>
import axios from "axios";
import router from "@/router";

export default {
  name: "InitialSetup",
  data () {
    return {
      username: '',
      email: '',
      password: '',
      confirm_password: ''
    }
  },
  methods: {
    saveForm() {
      if (this.password === this.confirm_password) {
        let payload = {
          username: this.username,
          email: this.email,
          password: this.password
        }
        axios.post('/api/initial_setup/create_user/', payload).then(() => {
          router.push({'name': 'home'})
        })
      }
    }
  }
}
</script>

<style scoped>

</style>
