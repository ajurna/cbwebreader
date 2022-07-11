import * as Vue from 'vue'
import App from './App.vue'
import ToastPlugin from 'vue-toast-notification';

import '@coreui/vue'
import '@coreui/coreui/dist/css/coreui.min.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'vue-toast-notification/dist/theme-default.css';

/* import the fontawesome core */
import { library } from '@fortawesome/fontawesome-svg-core'

/* import font awesome icon component */
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/* import specific icons */
import { fas } from '@fortawesome/free-solid-svg-icons'
library.add(fas)

import router from './router'
import store from './store'

/* add icons to the library */
import axios from 'axios'
import VueAxios from 'vue-axios'


Vue.createApp(App).use(ToastPlugin).use(store).use(VueAxios, axios).use(router).component('font-awesome-icon', FontAwesomeIcon).mount('#app')
