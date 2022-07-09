<template>
  <CContainer>
    <CRow>
      <CCol lg="4"/>
      <CCol lg="4">
        <CForm>
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
            />
            <CButton @click="login" color="primary" class="mb-3">Login</CButton>
        </CForm>
      </CCol>
    </CRow>
  </CContainer>
</template>

<script>
import {CContainer, CRow, CCol, CForm, CFormInput, CButton} from "@coreui/vue";
import axios from "axios";



export default {
  name: "LoginView",
  components: {
    CForm,
    CCol,
    CContainer,
    CRow,
    // CFormLabel,
    CFormInput,
    CButton
  },
  data() {
    return {
      username: '',
      password: '',
      csrfToken: ''
    }
  },
  methods: {
    login () {
      console.log('clicked login' + this.username + this.password)

      axios.post('http://localhost:8000/api/token/', {
        username: this.username,
        password: this.password
      })
      .then(function (response) {
        console.log(response);
      })
      .catch(function (error) {
        console.log(error);
      });
    }
  }
}
</script>

<style scoped>

</style>