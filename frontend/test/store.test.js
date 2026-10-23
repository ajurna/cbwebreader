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

describe('reader mode', () => {
  it('starts in paged mode when nothing is stored', async () => {
    vi.resetModules()
    const fresh = (await import('@/store')).default

    expect(fresh.state.reader_mode).toBe('paged')
  })

  it('keeps the chosen mode in localStorage', () => {
    store.commit('setReaderMode', 'scroll')

    expect(store.state.reader_mode).toBe('scroll')
    expect(localStorage.getItem('reader_mode')).toBe('scroll')
  })

  it('ignores a mode it does not recognise', () => {
    store.commit('setReaderMode', 'scroll')
    store.commit('setReaderMode', 'banana')

    expect(store.state.reader_mode).toBe('scroll')
    expect(localStorage.getItem('reader_mode')).toBe('scroll')
  })
})

describe('reader page size', () => {
  it('fits the page to the width at full scale when nothing is stored', async () => {
    // An earlier test in this file may have stored a choice, so start from nothing.
    localStorage.removeItem('reader_fit')
    localStorage.removeItem('reader_zoom')
    vi.resetModules()
    const fresh = (await import('@/store')).default

    expect(fresh.state.reader_fit).toBe('width')
    expect(fresh.state.reader_zoom).toBe(100)
  })

  it('keeps the chosen size in localStorage', () => {
    store.commit('setReaderFit', 'page')
    store.commit('setReaderZoom', 150)

    expect(store.state.reader_fit).toBe('page')
    expect(store.state.reader_zoom).toBe(150)
    expect(localStorage.getItem('reader_fit')).toBe('page')
    expect(localStorage.getItem('reader_zoom')).toBe('150')
  })

  it('keeps a zoom it was asked for within its bounds', () => {
    store.commit('setReaderZoom', 10)
    expect(store.state.reader_zoom).toBe(25)

    store.commit('setReaderZoom', 500)
    expect(store.state.reader_zoom).toBe(200)

    // A value that is not a number is not a zoom, so nothing is kept.
    store.commit('setReaderZoom', 'banana')
    expect(store.state.reader_zoom).toBe(200)
  })

  it('ignores a size it does not recognise', () => {
    store.commit('setReaderFit', 'page')
    store.commit('setReaderFit', 'banana')

    expect(store.state.reader_fit).toBe('page')
    expect(localStorage.getItem('reader_fit')).toBe('page')
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

  it('slides the window while opening the app, so an idle tab is not a timeout', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.get.mockResolvedValue({ data: { id: 1, is_superuser: false } })
    api.post.mockResolvedValue({ data: {} })

    await store.dispatch('restoreSession')

    expect(store.state.user).toEqual({ id: 1, is_superuser: false })
    // The refresh token is single use on the server, so spending it here is what moves
    // the session forward from this visit instead of leaving it to age until it ends.
    expect(api.post).calledWith('/api/token/refresh/', {})
    expect(api.post).toHaveBeenCalledTimes(1)
  })

  it('ends the session when the window cannot be slid', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.get.mockResolvedValue({ data: { id: 1, is_superuser: false } })
    api.post.mockRejectedValue({ response: { status: 401 } })

    await store.dispatch('restoreSession')

    // The profile is still known, but the session is over, so the reader is sent to login
    // rather than sitting on a page whose every request fails.
    expect(store.getters.isAuthenticated).toBe(false)
    expect(router.push).toHaveBeenCalledWith({
      name: 'login',
      query: {
        next: '/account',
        error: 'Your session has expired. Please log in again.',
      },
    })
  })
})

describe('token handling', () => {
  it('rejects and logs out when the refresh cookie is no longer valid', async () => {
    store.commit('updateUser', { id: 1, is_superuser: false })
    api.post.mockRejectedValue({ response: { status: 401 } })

    await expect(store.dispatch('refreshToken')).rejects.toBeTruthy()

    expect(store.getters.isAuthenticated).toBe(false)
    // The page they were on, not the address of the API call that failed - an API address has
    // no page to show, so going back to one after logging in is a blank screen.
    expect(router.push).toHaveBeenCalledWith({
      name: 'login',
      query: {
        next: '/account',
        error: 'Your session has expired. Please log in again.',
      },
    })
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
