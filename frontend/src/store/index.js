import { createStore } from 'vuex'
import axios from 'axios'
import jwtDecode from 'jwt-decode'
import {useToast} from "vue-toast-notification";
import router from "@/router";

function get_jwt_from_storage(){
  try {
    return JSON.parse(localStorage.getItem('t'))
  } catch {
    return null
  }
}

export default createStore({
  state: {
    jwt: get_jwt_from_storage(),
    base_url: 'http://localhost:8000',
  },
  getters: {
  },
  mutations: {
    updateToken(state, newToken){
      localStorage.setItem('t', JSON.stringify(newToken));
      state.jwt = newToken;
    },
    removeToken(state){
      localStorage.removeItem('t');
      state.jwt = null;
    }
  },
  actions: {
    obtainToken(context, {username, password}){
      const payload = {
        username: username,
        password: password
      }
      axios.post(this.state.base_url+'/api/token/', payload)
        .then((response)=>{
            context.commit('updateToken', response.data);
            router.push('/')
          })
        .catch((error)=>{
            console.log(error);
            const $toast = useToast();
            $toast.error(error.response.data.detail, {position:'top'});
          })
    },
    refreshToken(){
      const payload = {
        refresh: this.state.jwt.refresh
      }
      return axios.post(this.state.base_url + '/api/token/refresh/', payload)
        .then((response)=>{
            this.commit('updateToken', response.data)
          })
        .catch((error)=>{
            console.log(error)
            router.push('/login')
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
