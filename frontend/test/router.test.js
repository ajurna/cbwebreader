import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api', () => ({ default: { get: vi.fn(), post: vi.fn() } }))

import store from '@/store'
import router from '@/router'

beforeEach(() => {
  localStorage.clear()
  store.commit('logOut')
})

describe('navigation guards', () => {
  it('redirects an anonymous user to the login page', async () => {
    await router.push('/account')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.error).toBe('Please log in to access this page')
  })

  it('keeps the requested path so the user returns there after logging in', async () => {
    await router.push('/history')

    expect(router.currentRoute.value.query.next).toBe('/history')
  })

  it('allows an authenticated non-admin to reach the history page', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })

    await router.push('/history')

    expect(router.currentRoute.value.name).toBe('history')
  })

  it('still requires admin for the user page', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })

    await router.push('/user')

    expect(router.currentRoute.value.name).toBe('login')
  })

  it('allows an admin on the user page', async () => {
    store.commit('updateUser', { id: 1, is_superuser: true })

    await router.push('/user')

    expect(router.currentRoute.value.name).toBe('user')
  })
})
