import { createStore } from 'vuex'
import axios from 'axios'
import { jwtDecode } from "jwt-decode";
import {useToast} from "vue-toast-notification";
import router from "@/router";
import api from "@/api";

// We'll no longer use localStorage for tokens
// Instead, tokens will be stored in httpOnly cookies by the backend
// and automatically included in requests
function get_jwt_from_storage(){
  return null; // Initial state will be null until login
}
function get_user_from_storage(){
  try {
    return JSON.parse(localStorage.getItem('u'))
  } catch {
    return null
  }
}

export default createStore({
  state: {
    jwt: get_jwt_from_storage(),
    filters: {},
    user: get_user_from_storage(),
    classifications: [
      {label: 'G', value: '0'},
      {label: 'PG', value: '1'},
      {label: '12', value: '2'},
      {label: '15', value: '3'},
      {label: '18', value: '4'},
    ],
  },
  getters: {
    is_superuser (state) {
      if (state.user === null){
        return false
      } else {
        return state.user.is_superuser
      }
    }
  },
  mutations: {
    updateToken(state, newToken){
      // No longer storing tokens in localStorage
      // Tokens are stored in httpOnly cookies by the backend
      state.jwt = newToken;
    },
    logOut(state){
      // Clear user data from localStorage
      localStorage.removeItem('u')
      // Clear state

      // Make a request to the backend to invalidate the token
      axios.post('/api/token/blacklist/', { refresh: state.jwt?.refresh })
        .catch(error => console.error('Error blacklisting token:', error));
      state.jwt = null;
      state.user = null
    },
    updateUser(state, userData){
      localStorage.setItem('u', JSON.stringify(userData));
      state.user = userData
    },
  },
  actions: {
    obtainToken(context, {username, password}){
      const payload = {
        username: username,
        password: password
      }
      axios.post('/api/token/', payload)
        .then((response)=>{
            context.commit('updateToken', response.data);
            api.get('/api/account').then(response => {
              context.commit('updateUser', response.data)
            })
            if ('next' in router.currentRoute.value.query) {
              router.push(router.currentRoute.value.query.next)
            } else {
              router.push('browse')
            }

          })
        .catch((error)=>{
            const $toast = useToast();
            if (error.response.data.detail) {
              $toast.error(error.response.data.detail, {position:'top'});
            }
            if (error.response.data.username) {
              $toast.error("Username: " + error.response.data.username, {position:'top'});
            }
            if (error.response.data.password) {
              $toast.error("Password: " + error.response.data.password, {position:'top'});
            }

          })
    },
    refreshToken(){
      // Don't attempt to refresh if we don't have a token
      if (!this.state.jwt || !this.state.jwt.refresh) {
        return Promise.reject(new Error('No refresh token available'));
      }

      const payload = {
        refresh: this.state.jwt.refresh
      }

      return axios.post('/api/token/refresh/', payload)
        .then((response) => {
          this.commit('updateToken', response.data);
          return response.data;
        })
        .catch((error) => {
          console.error('Token refresh failed:', error);
          // If refresh fails, log the user out and redirect to login
          this.commit('logOut');
          router.push({
            name: 'login',
            query: {
              next: router.currentRoute.value.fullPath,
              error: 'Your session has expired. Please log in again.'
            }
          });
          return Promise.reject(error);
        });
    },
    inspectToken(){
      const token = this.state.jwt;
      if (!token) return;

      try {
        // For access token
        const decoded = jwtDecode(token.access);
        const exp = decoded.exp;
        const now = Date.now() / 1000;

        // Refresh when token is within 5 minutes of expiring
        const refreshThreshold = 300; // 5 minutes in seconds

        if (exp - now < refreshThreshold) {
          // Token is about to expire, refresh it
          this.dispatch('refreshToken');
        } else if (exp < now) {
          // Token is already expired, force logout
          this.commit('logOut');
          router.push({
            name: 'login',
            query: {
              next: router.currentRoute.value.fullPath,
              error: 'Your session has expired. Please log in again.'
            }
          });
        }
      } catch (error) {
        console.error('Error inspecting token:', error);
        // If we can't decode the token, log the user out
        this.commit('logOut');
        router.push({name: 'login'});
      }
    }
  },
  modules: {
  }
})
