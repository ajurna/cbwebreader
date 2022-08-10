<template>
  <CButton color="secondary" @click="visible = true">Add User</CButton>
  <CModal :visible="visible" @close="visible = false">
    <CModalHeader>
      <CModalTitle>Add user</CModalTitle>
    </CModalHeader>
    <CForm @submit="addUser">
      <CModalBody>
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
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" @click="visible = false">
          Close
        </CButton>
        <CButton color="primary" type="submit">Submit</CButton>
      </CModalFooter>
    </CForm>
  </CModal>
</template>

<script>
import api from "@/api";
export default {
  name: "AddUser",
  data() {
    return {
      visible: false,
      username: '',
      email: ''
    }
  },
  props: {
    messages: Array,
    updateUsers: {}
  },
  methods: {
    addUser(e) {
      console.log(e)

      let payload = {
        username: this.username,
        email: this.email
      }
      api.post('/api/users/', payload).then(response => {
        payload = {
          username: response.data.username
        }
        api.patch('/api/users/' + response.data.id + '/reset_password/', payload).then(response2 => {
          this.messages.push({
            color: 'success',
            text: 'New user "' + response.data.username + '" created with password "' + response2.data.password + '".'
          })
          this.updateUsers()
          this.visible=false
        })
      })
    }
  }
}
</script>

<style scoped>

</style>