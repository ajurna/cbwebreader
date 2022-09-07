<template>
  <button type="button" class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#addUserModal">Add User</button>

  <div class="modal fade" id="addUserModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true" >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="exampleModalLabel">Add user</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form @submit="addUser">
          <div class="modal-body">
            <div class="mb-3">
              <label for="usernameInput" class="form-label">Username</label>
              <input type="text" class="form-control" id="usernameInput" aria-describedby="usernameHelp" v-model="username">
              <div id="usernameHelp" class="form-text">Please enter a unique username</div>
            </div>
            <div class="mb-3">
              <label for="emailInput" class="form-label">Email address</label>
              <input type="email" class="form-control" id="emailInput" aria-describedby="emailHelp" v-model="email">
              <div id="emailHelp" class="form-text">Must be 8-20 characters long.</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="submit" class="btn btn-primary" data-bs-dismiss="modal">Submit</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/api";
import 'bootstrap/js/dist/modal'
export default {
  name: "AddUser",
  data() {
    return {
      username: '',
      email: ''
    }
  },
  props: {
    messages: Array,
  },
  methods: {
    addUser() {
      let payload = {
        username: this.username,
        email: this.email
      }
      api.post('/api/users/', payload).then(response => {
        payload = {
          username: response.data.username
        }
        api.patch('/api/users/' + response.data.id + '/reset_password/', payload).then(response2 => {
          this.$emit('add-message', {
            color: 'success',
            text: 'New user "' + response.data.username + '" created with password "' + response2.data.password + '".'
          })
          this.$emit('user-added')
        })
      }).catch(err => {
        this.$emit('add-message', {
          color: 'danger',
          text: 'Cannot create user "' + this.username + '" with error "' + (err.response.data.username? err.response.data.username: err.response.data.email) + '".'
        })
      })
    }
  },
  emits: ['user-added', 'add-message']
}
</script>

<style scoped>

</style>
