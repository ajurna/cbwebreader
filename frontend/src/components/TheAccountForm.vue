<template>
  <CContainer>
    <CForm @submit="updateAccount" >
      <CFormInput
        type="text"
        label="Username"
        readonly
        v-model="username"

      />
      <CFormInput
        type="email"
        label="Email address"
        :placeholder="email"
        text="Must be 8-20 characters long."
        v-model="email"
        feedback-invalid="Email address invalid."
        :valid="validateEmail(email)"
      />
      <CFormInput
        type="password"
        label="Current Password"
        placeholder="Enter Current Password"
        text="Must enter current password to change settings."
        v-model="current_password"
        feedback-invalid="Wrong Password."
        :valid="password_correct"
      />
      <CFormInput
        type="password"
        label="New Password"
        placeholder="Enter New Password"
        text="Must be at least 9 characters long."
        v-model="new_password"
        feedback-invalid="Password is not complex enough."
        :valid="checkNewPassword(new_password)"
      />
      <CFormInput
        type="password"
        label="New Password Confirm"
        placeholder="Enter New Password"
        text="Must be at least 9 characters long."
        v-model="new_password_confirm"
        feedback-invalid="New passwords should match."
        :valid="new_password === new_password_confirm"
      />
      <CButton color="primary" type="submit">Save</CButton>
    </CForm>
  </CContainer>
</template>

<script>
import {CForm, CFormInput, CContainer, CButton} from "@coreui/vue";
import api from "@/api";
import {useToast} from "vue-toast-notification";
const toast = useToast();
export default {
  name: "TheAccountForm",
  components: {
    CForm,
    CFormInput,
    CContainer,
    CButton
  },
  data () {
    return {
      username: '',
      email: '',
      current_password: '',
      new_password: '',
      new_password_confirm: '',
      password_correct: false
    }
  },
  mounted() {
    api.get('/api/account/').then(response => {
      this.$store.commit('updateUser', response.data)
      this.username = this.$store.state.user.username
      this.email = this.$store.state.user.email
    })

  },
  methods: {
    updateAccount (data) {
      if (!this.current_password) {
        toast.success('form submitted', {position:'top'});
        return
      }
      // console.log(data)
    },
    validateEmail(mail){
      return (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(mail))
    },
    checkNewPassword(pass){
      return (pass.length >= 9)
    }
  }
}
</script>

<style scoped>

</style>