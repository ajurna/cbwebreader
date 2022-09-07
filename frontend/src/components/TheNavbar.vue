<template>
  <nav class="navbar navbar-expand-lg bg-light">
    <div class="container-fluid">
      <a class="navbar-brand" href="#"><img src="/static/img/logo.svg" width="35" class="d-inline-block align-top" alt="CB"> Web Reader</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link :to="{name: 'browse'}" class="nav-link" >Browse</router-link>
          </li>
          <li class="nav-item">
            <router-link :to="{name: 'recent'}" class="nav-link" >Recent</router-link>
          </li>
          <li class="nav-item">
            <router-link :to="{name: 'account'}" class="nav-link" >Account</router-link>
          </li>
          <li class="nav-item">
            <router-link :to="{name: 'user'}" class="nav-link" v-if="this.$store.getters.is_superuser">Users</router-link>
          </li>
          <li class="nav-item">
            <a class="nav-link" @click="logout">Log Out</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
<script>
import store from "@/store";
import router from "@/router";
import 'bootstrap/js/dist/collapse'
export default {
  name: "TheNavbar",
  components: { },
  data() {
    return {
      visible: false
    }
  },
  methods: {
    logout () {
      store.commit('logOut')
      router.push({name: 'login'})
    }
  }
}
</script>

<style scoped>
.nav-link {
  cursor: pointer;
}
</style>
