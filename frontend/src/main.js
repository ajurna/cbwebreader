import * as Vue from 'vue'
import App from './App.vue'
import ToastPlugin from 'vue-toast-notification';
import 'vue-toast-notification/dist/theme-default.css';

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/js/dist/dropdown'



/* import the fontawesome core */
import { library } from '@fortawesome/fontawesome-svg-core'

/* import font awesome icon component */
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/* import specific icons */
import {faBook, faBookOpen, faEdit, faTurnUp, faTimes, faCheck, faRefresh} from '@fortawesome/free-solid-svg-icons'
library.add(faBook, faBookOpen, faEdit, faTurnUp, faTimes, faCheck, faRefresh)

import router from './router'
import store from './store'

const app = Vue.createApp(App)
    .use(ToastPlugin)
    .use(store)
    .use(router)
    .component('font-awesome-icon', FontAwesomeIcon)

// Validate the cookie before the first navigation, so the router guards see the
// real session instead of whatever is left in localStorage.
store.dispatch('restoreSession').finally(() => {
    app.mount('#app')
})
