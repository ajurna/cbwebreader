import { createApp } from 'vue'
import App from './App.vue'
import '@coreui/vue'
import '@coreui/coreui/dist/css/coreui.min.css'
import 'bootstrap/dist/css/bootstrap.min.css'

/* import the fontawesome core */
import { library } from '@fortawesome/fontawesome-svg-core'

/* import font awesome icon component */
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/* import specific icons */
import { fas } from '@fortawesome/free-solid-svg-icons'
library.add(fas)

import router from './router'

/* add icons to the library */



createApp(App).use(router).component('font-awesome-icon', FontAwesomeIcon).mount('#app')
