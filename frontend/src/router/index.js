import { createRouter, createWebHashHistory } from 'vue-router'
import store from '@/store'

const ReadView = () => import('@/views/ReadView')
const RecentView = () => import('@/views/RecentView')
const AccountView = () => import('@/views/AccountView')
const BrowseView = () => import('@/views/BrowseView')
const UserView = () => import('@/views/UserView')
const LoginView = () => import('@/views/LoginView')
const HistoryView = () => import('@/views/HistoryView')

// Navigation guard to check if user is authenticated
function requireAuth(to) {
  if (!store.getters.isAuthenticated) {
    return {
      name: 'login',
      query: { next: to.fullPath, error: 'Please log in to access this page' }
    };
  }
}

// Navigation guard to check if user is admin
function requireAdmin(to) {
  if (!store.getters.isAuthenticated || !store.getters.is_superuser) {
    return {
      name: 'login',
      query: { next: to.fullPath, error: 'Admin access required' }
    };
  }
}

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
    props: true,
    beforeEnter: requireAuth
  },
  {
    path: '/read/:selector',
    name: 'read',
    component: ReadView,
    props: true,
    beforeEnter: requireAuth
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/recent',
    name: 'recent',
    component: RecentView,
    beforeEnter: requireAuth
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView,
    beforeEnter: requireAuth
  },
  {
    path: '/account',
    name: 'account',
    component: AccountView,
    beforeEnter: requireAuth
  },
  {
    path: '/user/:userid?',
    name: 'user',
    component: UserView,
    props: true,
    beforeEnter: requireAdmin
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
