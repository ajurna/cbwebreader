<template>
  <CContainer>
    <CRow>
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
  </CContainer>
</template>

<script>
import {CContainer, CRow, CCol, CForm, CFormInput, CButton} from "@coreui/vue";

export default {
  name: "LoginView",
  components: {
    CForm,
    CCol,
    CContainer,
    CRow,
    CFormInput,
    CButton,
  },
  data() {
    return {
      username: '',
      password: '',
      password_alert: false
    }
  },
  methods: {
    login () {
      this.$store.dispatch("obtainToken", {username: this.username, password: this.password})
    }
  }
}
</script>

<style scoped>

</style>