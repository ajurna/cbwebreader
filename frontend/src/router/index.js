import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from "@/views/LoginView";
import ReadView from "@/views/ReadView";

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    props: {selector: ''}
  },
  {
    path: '/browse/:selector',
    name: 'browse',
    component: HomeView,
    props: true
  },
  {
    path: '/read/:selector',
    name: 'read',
    component: ReadView,
    props: true
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/about',
    name: 'about',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(process.env.BASE_URL),
  routes
})

export default router
