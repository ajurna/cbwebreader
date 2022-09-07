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
import {faBook, faBookOpen, faEdit, faTurnUp, faTimes, faCheck} from '@fortawesome/free-solid-svg-icons'
library.add(faBook, faBookOpen, faEdit, faTurnUp, faTimes, faCheck)

import router from './router'
import store from './store'

Vue.createApp(App)
    .use(ToastPlugin)
    .use(store)
    .use(router)
    .component('font-awesome-icon', FontAwesomeIcon)
    .mount('#app')
