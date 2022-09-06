<template>
  <div class="container">
    <form @submit="saveForm">
      <label class="form-label">Username</label>
      <input class="form-control" readonly="" type="text" v-model="username" />

      <label class="form-label">Email address</label>
      <input placeholder="" class="form-control" type="email" v-model="email"/>

      <label class="form-label">Classification</label>
      <select aria-label="Default select example" class="form-select" v-model="classification">
        <option v-for="class_opt in [...this.$store.state.classifications]" :key="class_opt.value" :value="class_opt.value">{{class_opt.label}}</option>
      </select>

      <div class="row mt-2">
        <div class="col">
          <button type="submit" class="btn btn-primary me-5">Save</button>
          <confirm-button class="me-5" label="Reset Password" :action="resetPassword" />
          <confirm-button label="Delete User" :action="deleteUser" />
        </div>
      </div>
    </form>
  </div>
</template>

<script>

import api from "@/api";
import ConfirmButton from "@/components/ConfirmButton";
import router from "@/router";

export default {
  name: "UserEdit",
  components: {ConfirmButton},
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
  },
  methods: {
    saveForm () {
      if (this.email !== this.user.email){
        let payload = {
          username: this.username,
          email: this.email
        }
        api.patch('/api/users/'+ this.user.id + '/', payload).then(response => {
          this.$emit('add-message',{
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
          this.$emit('add-message', {
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
        this.$emit('add-message', {
          color: 'success',
          text: 'Password reset with new password "' + response.data.password + '"'
        })
        this.new_password = response.data.password
      })
    },
    deleteUser() {
      api.delete('/api/users/' + this.user.id + '/').then(() => {
        this.$emit('add-message', {
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
