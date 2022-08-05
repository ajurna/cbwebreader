import { createRouter, createWebHashHistory } from 'vue-router'
import LoginView from "@/views/LoginView";
import ReadView from "@/views/ReadView";
import RecentView from "@/views/RecentView";
import AccountView from "@/views/AccountView";
import BrowseView from "@/views/BrowseView";

const routes = [
  {
    path: '/',
    redirect: () => {
      return { name: 'browse' }
    }
  },
  {
    path: '/browse/:selector?',
    name: 'browse',
    component: BrowseView,
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
    path: '/recent',
    name: 'recent',
    component: RecentView
  },
  {
    path: '/account',
    name: 'account',
    component: AccountView
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
