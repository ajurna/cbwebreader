<template>
  <CContainer>
    <CRow v-if="!initialSetupRequired">
      <CCol lg="4"/>
      <CCol lg="4" id="login-col">
        <CForm @submit="login">
          <CFormInput
              type="username"
              id="username"
              label="Username"
              placeholder="username"
              text="Please enter your username"
              aria-describedby="loginFormControlInputHelpInline"
              v-model="username"
            />
            <CFormInput
              type="password"
              id="password"
              label="password"
              placeholder="password"
              text="Please enter your password"
              aria-describedby="loginFormControlInputHelpInline"
              v-model="password"
              @keyup.enter="login"
            />
            <CButton color="primary" class="mb-3">Login</CButton>
        </CForm>
      </CCol>
    </CRow>
    <CRow>
      <initial-setup v-if="initialSetupRequired" />
    </CRow>
  </CContainer>
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