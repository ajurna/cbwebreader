import axios from "axios";
import router from "@/router";
import store from "@/store";
import jwtDecode from "jwt-decode";

async function get_access_token() {
    let access = jwtDecode(store.state.jwt.access)
    let refresh = jwtDecode(store.state.jwt.refresh)
    if (access.exp - Date.now()/1000 < 5) {
        if (refresh.exp - Date.now()/1000 < 5) {
            await router.push({name: 'login'})
            return null
        } else {
            return store.dispatch('refreshToken').then(() => {return store.state.jwt.access})
        }
    }
    return store.state.jwt.access
    }

const axios_jwt = axios.create();

axios_jwt.interceptors.request.use(async function (config) {
    let access_token = await get_access_token().catch(() => {
        if (router.currentRoute.value.fullPath.includes('login')){
            router.push({name: 'login'})
        }else {
            router.push({name: 'login', query: { next: router.currentRoute.value.fullPath }})
        }

    })
    config.headers = {
        Authorization: "Bearer " + access_token
    }
    return config
    }, function (error) {
    // Do something with request error
    return Promise.reject(error);
    });

export default axios_jwt
