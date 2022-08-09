<template>
  <CContainer>
    <messages :messages="messages"></messages>
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
        v-model="usermisc"
        :options="[
            'Please Select a classification limit',
            ...this.$store.state.classifications
        ]">
      </CFormSelect>
      <CRow class="mt-2">
        <CCol>
          <CButton color="primary" type="submit" class="mr-5">Save</CButton>
          <confirm-button label="Reset Password" :action="resetPassword"/>
        </CCol>
      </CRow>

    </CForm>
  </CContainer>
</template>

<script>

import api from "@/api";
import ConfirmButton from "@/components/ConfirmButton";
import Messages from "@/components/Messages";

export default {
  name: "UserEdit",
  components: {Messages, ConfirmButton},
  data () {
    return {
      username: '',
      email: '',
      usermisc: '0',
      new_password: null,
      messages: []
    }
  },
  props: {
    user: Object
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
      if (this.usermisc !== this.user.usermisc.toString()){
        let payload = {
          username: this.username,
          classification: this.usermisc
        }
        console.log(this.usermisc)
        api.patch('/api/users/' + this.user.id + '/set_classification/', payload).then(response => {
          this.messages.push({
            color: 'success',
            text: 'Classification Limit now set to "' + this.$store.state.classifications.find(i => i.value === response.data.classification).label + '"'
          })
          // this.usermisc = response.data.classification.toString()
          // this.user.usermisc = response.data.classification
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
    }
  },
  beforeUnmount() {
    this.new_password = null
  },
  mounted() {
    this.username = this.user.username
    this.email = this.user.email
    this.usermisc = this.user.usermisc.toString()
  }
}
</script>

