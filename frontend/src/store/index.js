import { createStore } from 'vuex'
import {useToast} from "vue-toast-notification";
import router from "@/router";
import api from "@/api";

// Tokens live in HttpOnly cookies set by the backend, so JavaScript cannot read
// them. Only the user profile is kept in localStorage, to avoid a blank page
// before the first request has been made.
function get_user_from_storage(){
  try {
    return JSON.parse(localStorage.getItem('u'))
  } catch {
    return null
  }
}

// Reading mode is a preference rather than part of the session, so it is kept on its own.
function get_reader_mode_from_storage(){
  const mode = localStorage.getItem('reader_mode')
  return mode === 'scroll' ? 'scroll' : 'paged'
}

function session_expired_query(next){
  return {
    name: 'login',
    query: {
      next: next,
      error: 'Your session has expired. Please log in again.'
    }
  }
}

export default createStore({
  state: {
    filters: {},
    user: get_user_from_storage(),
    reader_mode: get_reader_mode_from_storage(),
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
    },
    isAuthenticated (state) {
      return state.user !== null
    }
  },
  mutations: {
    logOut(state){
      localStorage.removeItem('u')
      state.user = null
    },
    updateUser(state, userData){
      localStorage.setItem('u', JSON.stringify(userData));
      state.user = userData
    },
    setReaderMode(state, mode){
      if (mode !== 'paged' && mode !== 'scroll') {
        return
      }
      localStorage.setItem('reader_mode', mode);
      state.reader_mode = mode
    },
  },
  actions: {
    obtainToken(context, {username, password}){
      const payload = {
        username: username,
        password: password
      }
      // The response body is empty: the backend stores the tokens as HttpOnly cookies.
      api.post('/api/token/', payload)
        .then(() => api.get('/api/account'))
        .then((response) => {
          context.commit('updateUser', response.data)
          if ('next' in router.currentRoute.value.query) {
            router.push(router.currentRoute.value.query.next)
          } else {
            router.push('browse')
          }
        })
        .catch((error) => {
          const $toast = useToast();
          const data = error.response?.data ?? {};
          if (data.detail) {
            $toast.error(data.detail, {position:'top'});
          }
          if (data.username) {
            $toast.error("Username: " + data.username, {position:'top'});
          }
          if (data.password) {
            $toast.error("Password: " + data.password, {position:'top'});
          }
        })
    },
    refreshToken(){
      if (!this.state.user) {
        return Promise.reject(new Error('Not logged in'));
      }

      // The refresh token is read from the cookie by the backend.
      return api.post('/api/token/refresh/', {})
        .then((response) => response.data)
        .catch((error) => {
          console.error('Token refresh failed:', error);
          this.commit('logOut');
          router.push(session_expired_query(router.currentRoute.value.fullPath));
          return Promise.reject(error);
        });
    },
    // Check that the cookie still identifies the user stored in localStorage.
    restoreSession(){
      if (!this.state.user) {
        return Promise.resolve(null);
      }

      return api.get('/api/account')
        .then((response) => {
          this.commit('updateUser', response.data);
          return response.data;
        })
        .catch((error) => {
          if (error.response?.status === 401) {
            this.commit('logOut');
            router.push({ name: 'login' });
          }
          return null;
        });
    },
    logout(){
      const wasLoggedIn = this.state.user !== null;
      this.commit('logOut');

      if (!wasLoggedIn) {
        return Promise.resolve(null);
      }

      return api.post('/api/token/blacklist/', {})
        .catch((error) => {
          console.error('Error blacklisting token:', error);
        });
    }
  },
  modules: {
  }
})
