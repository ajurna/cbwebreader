<template>
  <CContainer>
    <CForm @submit="updateAccount">
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
        :valid="current_password.length > 0"
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
        :valid="new_password === new_password_confirm && new_password.length > 8"
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
    }
  },
  mounted() {
    this.updateFromServer()
  },
  methods: {
    updateFromServer() {
      api.get('/api/account/').then(response => {
        this.$store.commit('updateUser', response.data)
        this.username = this.$store.state.user.username
        this.email = this.$store.state.user.email
        this.current_password = ''
        this.new_password = ''
        this.new_password_confirm = ''
      })
    },
    updateAccount () {
      if (!this.current_password) {
        toast.error('Please enter your current password.', {position:'top'});
      } else {
        if (this.email !== this.$store.state.user.email) {
          let payload = {
            username: this.username,
            email: this.email,
            password: this.current_password
          }
          api.patch('/api/account/update_email/', payload).then(() => {
            toast.success('Email Address updated')
            this.updateFromServer()
          }).catch(error => {
            toast.error(error.response.data.errors)
          })
        }
        if (this.new_password === this.new_password_confirm) {
          let payload = {
            username: this.username,
            old_password: this.current_password,
            new_password: this.new_password,
            new_password_confirm: this.new_password_confirm
          }
          api.patch('/api/account/reset_password/', payload).then(() => {
            toast.success('Password reset successfully')
            this.updateFromServer()
          }).catch(error => {
            console.log(error.response.data)
            toast.error(error.response.data.errors)
          })
        }

      }
    },
    validateEmail(mail){
      return (/\S+@\S+\.\S+/.test(mail))
    },
    checkNewPassword(pass){
      return (pass.length >= 9)
    }
  }
}
</script>

<style scoped>

</style>