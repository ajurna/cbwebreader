import { createStore } from 'vuex'
import axios from 'axios'
import jwtDecode from 'jwt-decode'
import {useToast} from "vue-toast-notification";
import router from "@/router";
import api from "@/api";

function get_jwt_from_storage(){
  try {
    return JSON.parse(localStorage.getItem('t'))
  } catch {
    return null
  }
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
      localStorage.setItem('t', JSON.stringify(newToken));
      state.jwt = newToken;
    },
    logOut(state){
      localStorage.removeItem('t');
      localStorage.removeItem('u')
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
      const payload = {
        refresh: this.state.jwt.refresh
      }
      return axios.post('/api/token/refresh/', payload)
        .then((response)=>{
            this.commit('updateToken', response.data)
          })
        .catch((error)=>{
            console.log(error)
            // router.push({name: 'login', query: {area: 'store'}})
          })
    },
    inspectToken(){
      const token = this.state.jwt;
      if(token){
        const decoded = jwtDecode(token);
        const exp = decoded.exp
        const orig_iat = decoded.iat
        if(exp - (Date.now()/1000) < 1800 && (Date.now()/1000) - orig_iat < 628200){
          this.dispatch('refreshToken')
        } else if (exp -(Date.now()/1000) < 1800){
          // DO NOTHING, DO NOT REFRESH
        } else {
          // PROMPT USER TO RE-LOGIN, THIS ELSE CLAUSE COVERS THE CONDITION WHERE A TOKEN IS EXPIRED AS WELL
        }
      }
    }
  },
  modules: {
  }
})
