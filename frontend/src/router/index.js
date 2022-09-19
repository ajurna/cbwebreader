import { createRouter, createWebHashHistory } from 'vue-router'

const ReadView = () => import('@/views/ReadView')
const RecentView = () => import('@/views/RecentView')
const AccountView = () => import('@/views/AccountView')
const BrowseView = () => import('@/views/BrowseView')
const UserView = () => import('@/views/UserView')
const LoginView = () => import('@/views/LoginView')
const HistoryView = () => import('@/views/HistoryView')

const routes = [
  {
    path: '/',
    name: 'home',
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
    path: '/history',
    name: 'history',
    component: HistoryView
  },
  {
    path: '/account',
    name: 'account',
    component: AccountView
  },
  {
    path: '/user/:userid?',
    name: 'user',
    component: UserView,
    props: true
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
