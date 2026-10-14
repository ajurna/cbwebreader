import { beforeEach, describe, expect, it, vi } from 'vitest'

const { api, router } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn() },
  router: { currentRoute: { value: { query: {}, fullPath: '/account' } }, push: vi.fn() },
}))

vi.mock('@/api', () => ({ default: api }))
vi.mock('@/router', () => ({ default: router }))

import store from '@/store'

beforeEach(() => {
  localStorage.clear()
  store.commit('logOut')
  api.get.mockReset()
  api.post.mockReset()
  router.push.mockReset()
})

describe('session state', () => {
  it('is not authenticated when there is no stored profile', () => {
    expect(store.getters.isAuthenticated).toBe(false)
    expect(store.getters.is_superuser).toBe(false)
  })

  it('keeps the profile in localStorage so a reload is not a blank page', () => {
    store.commit('updateUser', { id: 1, is_superuser: false })

    expect(store.getters.isAuthenticated).toBe(true)
    expect(JSON.parse(localStorage.getItem('u'))).toEqual({ id: 1, is_superuser: false })
  })

  it('logOut clears both the profile and localStorage', () => {
    store.commit('updateUser', { id: 1, is_superuser: true })
    store.commit('logOut')

    expect(store.getters.isAuthenticated).toBe(false)
    expect(localStorage.getItem('u')).toBeNull()
  })
})

describe('restoreSession', () => {
  it('refreshes the stored profile from the cookie session', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.get.mockResolvedValue({ data: { id: 1, is_superuser: true } })

    await store.dispatch('restoreSession')

    expect(api.get).toHaveBeenCalledWith('/api/account')
    expect(store.getters.is_superuser).toBe(true)
  })

  it('logs out when the cookie no longer identifies the user', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.get.mockRejectedValue({ response: { status: 401 } })

    await store.dispatch('restoreSession')

    expect(store.getters.isAuthenticated).toBe(false)
    expect(router.push).toHaveBeenCalledWith({ name: 'login' })
  })

  it('does nothing when there is no stored profile', async () => {
    await store.dispatch('restoreSession')

    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('token handling', () => {
  it('rejects and logs out when the refresh cookie is no longer valid', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.post.mockRejectedValue({ response: { status: 401 } })

    await expect(store.dispatch('refreshToken')).rejects.toBeTruthy()

    expect(store.getters.isAuthenticated).toBe(false)
    expect(router.push).toHaveBeenCalledWith(expect.objectContaining({ name: 'login' }))
  })

  it('does not call the API when there is no session', async () => {
    await expect(store.dispatch('refreshToken')).rejects.toBeTruthy()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('does not blacklist a token for a session that does not exist', async () => {
    await store.dispatch('logout')

    expect(api.post).not.toHaveBeenCalled()
    expect(store.getters.isAuthenticated).toBe(false)
  })

  it('blacklists the token when a session existed', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.post.mockResolvedValue({ data: {} })

    await store.dispatch('logout')

    expect(api.post).toHaveBeenCalledWith('/api/token/blacklist/', {})
    expect(store.getters.isAuthenticated).toBe(false)
  })
})
