import { beforeEach, describe, expect, it, vi } from 'vitest'

const { api, store, router, interceptors } = vi.hoisted(() => {
  const interceptors = { request: [], response: [] }
  const api = {
    request: vi.fn(),
    interceptors: {
      request: { use: (fn) => interceptors.request.push(fn) },
      response: { use: (ok, err) => interceptors.response.push({ ok, err }) },
    },
  }
  return {
    api,
    store: { dispatch: vi.fn(), commit: vi.fn() },
    router: { push: vi.fn() },
    interceptors,
  }
})

vi.mock('axios', () => ({ default: { create: () => api } }))
vi.mock('@/store', () => ({ default: store }))
vi.mock('@/router', () => ({ default: router }))

import axiosApi from '@/api'

const requestInterceptor = interceptors.request[0]
const { ok: successHandler, err: errorHandler } = interceptors.response[0]

function error401(url) {
  return { response: { status: 401 }, config: { url } }
}

beforeEach(() => {
  document.cookie = 'csrftoken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
  api.request.mockReset()
  store.dispatch.mockReset()
  store.commit.mockReset()
  router.push.mockReset()
})

describe('request interceptor', () => {
  it('uses the cookie session, so it sends no Authorization header', () => {
    expect(axiosApi).toBe(api)
    expect(requestInterceptor({ headers: {} }).headers).not.toHaveProperty('Authorization')
  })

  it('adds the CSRF header when a csrftoken cookie exists', () => {
    document.cookie = 'csrftoken=abc123; path=/'

    expect(requestInterceptor({ headers: {} }).headers['X-CSRFToken']).toBe('abc123')
  })

  it('leaves the headers untouched when there is no CSRF cookie', () => {
    expect(requestInterceptor({ headers: {} }).headers).not.toHaveProperty('X-CSRFToken')
  })
})

describe('response interceptor', () => {
  it('passes successful responses through', async () => {
    const response = { data: [1, 2] }

    expect(await successHandler(response)).toBe(response)
    expect(store.dispatch).not.toHaveBeenCalled()
  })

  it('refreshes the session and retries once after a 401', async () => {
    store.dispatch.mockResolvedValue(undefined)
    api.request.mockResolvedValue({ data: 'retried' })
    const error = error401('/api/browse/')

    expect(await errorHandler(error)).toEqual({ data: 'retried' })
    expect(store.dispatch).toHaveBeenCalledWith('refreshToken')
    expect(api.request).toHaveBeenCalledWith(error.config)
    expect(error.config._retried).toBe(true)
  })

  it('does not retry a request that has already been retried', async () => {
    const error = error401('/api/browse/')
    error.config._retried = true

    await expect(errorHandler(error)).rejects.toBe(error)
    expect(store.dispatch).not.toHaveBeenCalled()
  })

  it('does not retry the token endpoints, which would loop', async () => {
    const error = error401('/api/token/refresh/')

    await expect(errorHandler(error)).rejects.toBe(error)
    expect(store.dispatch).not.toHaveBeenCalled()
  })

  it('logs out and goes to the login page when the refresh fails', async () => {
    store.dispatch.mockRejectedValue(new Error('expired'))
    const error = error401('/api/browse/')

    await expect(errorHandler(error)).rejects.toBe(error)

    expect(store.commit).toHaveBeenCalledWith('logOut')
    expect(router.push).toHaveBeenCalledWith({
      name: 'login',
      query: {
        next: '/api/browse/',
        error: 'Your session has expired. Please log in again.',
      },
    })
  })

  it('leaves other error statuses alone', async () => {
    const error = { response: { status: 403 }, config: { url: '/api/browse/' } }

    await expect(errorHandler(error)).rejects.toBe(error)
    expect(store.dispatch).not.toHaveBeenCalled()
  })
})
