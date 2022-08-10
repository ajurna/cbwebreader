<template>
  <CContainer>
    <CForm @submit="saveForm">
      <CFormInput
        type="text"
        label="Username"
        readonly
        v-model="username"
      />
      <CFormInput
        type="email"
        label="Email address"
        :placeholder="user.email"
        text="Must be 8-20 characters long."
        v-model="email"
        feedback-invalid="Email address invalid."
      />
      <CFormSelect
        aria-label="Default select example"
        v-model="classification"
        :options="[...this.$store.state.classifications]">
      </CFormSelect>
      <CRow class="mt-2">
        <CCol>
          <CButton color="primary" type="submit" class="mr-5">Save</CButton>
          <confirm-button class="mr-5" label="Reset Password" :action="resetPassword" />
          <confirm-button label="Delete User" :action="deleteUser" />
        </CCol>
      </CRow>

    </CForm>
  </CContainer>
</template>

<script>

import api from "@/api";
import ConfirmButton from "@/components/ConfirmButton";
import Messages from "@/components/Messages";
import router from "@/router";

export default {
  name: "UserEdit",
  components: {Messages, ConfirmButton},
  data () {
    return {
      username: '',
      email: '',
      classification: '0',
      new_password: null,
    }
  },
  props: {
    user: Object,
    messages: Array,
  },
  methods: {
    saveForm () {
      if (this.email !== this.user.email){
        let payload = {
          username: this.username,
          email: this.email
        }
        api.patch('/api/users/'+ this.user.id + '/', payload).then(response => {
          this.messages.push({
            color: 'success',
            text: 'Email address now set to "' + response.data.email + '"'
          })
        })
      }
      if (this.classification !== this.user.classification.toString()){
        let payload = {
          username: this.username,
          classification: this.classification
        }
        api.patch('/api/users/' + this.user.id + '/set_classification/', payload).then(response => {
          this.messages.push({
            color: 'success',
            text: 'Classification Limit now set to "' + this.$store.state.classifications.find(i => i.value === response.data.classification.toString()).label + '"'
          })
        })
      }
    },
    resetPassword() {
      let payload = {
        username: this.username
      }
      api.patch('/api/users/' + this.user.id + '/reset_password/', payload).then(response => {
        this.messages.push({
          color: 'success',
          text: 'Password reset with new password "' + response.data.password + '"'
        })
        this.new_password = response.data.password
      })
    },
    deleteUser() {
      api.delete('/api/users/' + this.user.id + '/').then(response => {
        this.messages.push({
          color: 'danger',
          text: 'User "' + this.username + '" has been deleted.'
        })
        router.push({name: 'user'})
      })
    }
  },
  beforeUnmount() {
    this.new_password = null
  },
  mounted() {
    this.username = this.user.username
    this.email = this.user.email
    this.classification = this.user.classification.toString()
  }
}
</script>

