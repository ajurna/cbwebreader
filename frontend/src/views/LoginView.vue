<template>
  <div class="container">
    <div class="row" v-if="!initialSetupRequired">
      <div class="col col-lg-4" />
      <div class="col col-lg-4" id="login-col">
        <form @submit="login" v-on:submit.prevent="onSubmit">
          <label class="form-label" for="username">Username</label>
          <input id="username" placeholder="username" aria-describedby="loginFormControlInputHelpInline" class="form-control" type="text" v-model="username" />
          <div class="form-text" id="loginFormControlInputHelpInline">Please enter your username</div>

          <label class="form-label" for="password">password</label>
          <input id="password" placeholder="password" aria-describedby="loginFormControlInputHelpInline" class="form-control" type="password" v-model="password"/>
          <div class="form-text" id="loginFormControlInputHelpInline">Please enter your password</div>

          <button class="btn btn-primary mb-3" type="submit">Login</button>
        </form>
      </div>
    </div>
    <div class="row">
      <initial-setup v-if="initialSetupRequired" />
    </div>
  </div>
</template>

<script>
import InitialSetup from "@/components/InitialSetup";
import axios from "axios";

export default {
  name: "LoginView",
  components: {InitialSetup},
  data() {
    return {
      username: '',
      password: '',
      password_alert: false,
      initialSetupRequired: false
    }
  },
  methods: {
    login () {
      this.$store.dispatch("obtainToken", {username: this.username, password: this.password})
    }
  },
  mounted() {
    axios.get('/api/initial_setup/required/').then(response => {
      if (response.data.required){
        this.initialSetupRequired = true
      }
    })
  }
}
</script>

<style scoped>

</style>
