<template>
  <h1>Create your admin account.</h1>
  <CForm @submit="saveForm">
    <CFormInput
      type="text"
      label="Username"
      v-model="username"
    />
    <CFormInput
      type="email"
      label="Email address"
      text="Must be 8-20 characters long."
      v-model="email"
      feedback-invalid="Email address invalid."
    />
    <CFormInput
      type="password"
      label="Password"
      v-model="password"
    />
    <CFormInput
      type="password"
      label="Confirm Password"
      v-model="confirm_password"
    />
    <CButton color="primary" type="submit" class="mr-5 mt-2">Save</CButton>
  </CForm>
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