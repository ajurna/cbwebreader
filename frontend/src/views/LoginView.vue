<template>
  <div class="container">
    <div class="row" v-if="!initialSetupRequired">
      <div class="col col-lg-4" />
      <div class="col col-lg-4" id="login-col">
        <!-- Display error message if present -->
        <div class="alert alert-danger" v-if="errorMessage">
          {{ errorMessage }}
        </div>

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
      initialSetupRequired: false,
      errorMessage: ''
    }
  },
  methods: {
    login () {
      this.$store.dispatch("obtainToken", {username: this.username, password: this.password})
    }
  },
  mounted() {
    // Check for error message in route query params
    if (this.$route.query.error) {
      this.errorMessage = this.$route.query.error;
    }

    // Check if initial setup is required
    axios.get('/api/initial_setup/required/').then(response => {
      if (response.data.required){
        this.initialSetupRequired = true
      }
    })
  },
  // Clear error message when route changes
  watch: {
    '$route'(to) {
      this.errorMessage = to.query.error || '';
    }
  }
}
</script>

<style scoped>

</style>
