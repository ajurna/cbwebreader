<template>
  <div class="container">
    <form @submit="updateAccount">
      <label class="form-label">Username</label>
      <input class="form-control" readonly type="text" v-model="username" />

      <label class="form-label">Email address</label>
      <input placeholder="" class="form-control" type="email" v-model="email" />

      <label class="form-label">Current Password</label>
      <input placeholder="Enter Current Password" class="form-control" type="password" v-model="current_password"/>
      <div class="form-text">Must enter current password to change settings.</div>

      <label class="form-label">New Password</label><input placeholder="Enter New Password" class="form-control" type="password" v-model="new_password"/>
      <div class="form-text">Must be at least 9 characters long.</div>

      <label class="form-label">New Password Confirm</label><input placeholder="Enter New Password" class="form-control" type="password" v-model="new_password_confirm"/>
      <div class="form-text">Must be at least 9 characters long.</div>

      <button class="btn btn-primary" type="submit">Save</button>
    </form>

  </div>
</template>

<script>
import api from "@/api";
import {useToast} from "vue-toast-notification";
const toast = useToast();
export default {
  name: "TheAccountForm",
  components: {},
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
      } else if (this.email === this.$store.state.user.email && this.new_password.length === 0){
        toast.error('No changes detected', {position:'top'});
      } else {
        console.log(this.email === this.$store.state.user.email)
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
        if (this.new_password === this.new_password_confirm && this.new_password.length > 0) {
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
  }
}
</script>

<style scoped>

</style>
