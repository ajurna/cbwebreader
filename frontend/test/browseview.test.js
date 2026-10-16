import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import BrowseView from '@/views/BrowseView.vue'

const STUBS = {
  TheBreadcrumbs: { props: ['selector'], name: 'TheBreadcrumbs', template: '<div class="breadcrumbs" />' },
  TheComicList: { props: ['selector'], name: 'TheComicList', template: '<div class="comic-list" />' },
  TheContinueReading: { props: ['selector'], name: 'TheContinueReading', template: '<div class="continue-reading" :data-selector="selector" />' },
}

describe('BrowseView', () => {
  it('shows the continue reading panel on the home page', () => {
    const wrapper = mount(BrowseView, { props: { selector: '' }, global: { stubs: STUBS } })
    expect(wrapper.find('.continue-reading').exists()).toBe(true)
    expect(wrapper.find('.continue-reading').attributes('data-selector')).toBe('')
  })

  it('shows it inside a folder and passes the folder so it can be scoped', () => {
    const wrapper = mount(BrowseView, { props: { selector: 'abc' }, global: { stubs: STUBS } })
    expect(wrapper.find('.continue-reading').exists()).toBe(true)
    expect(wrapper.find('.continue-reading').attributes('data-selector')).toBe('abc')
  })
})
