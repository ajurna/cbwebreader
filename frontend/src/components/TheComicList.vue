<template>
  <CContainer>
    <CRow>
      <CInputGroup>
        <CFormInput placeholder="Search" aria-label="Filter comics by name" v-model="this.search_string"/>
        <CButton type="button" :color="(!this.filter_read && !this.filter_unread? 'primary' : 'secondary')" variant="outline" @click="this.filter_read=false; this.filter_unread=false">All</CButton>
        <CButton type="button" :color="(this.filter_read && !this.filter_unread? 'primary' : 'secondary')" variant="outline" @click="this.filter_read=true; this.filter_unread=false">Read</CButton>
        <CButton type="button" :color="(!this.filter_read && this.filter_unread? 'primary' : 'secondary')" variant="outline" @click="this.filter_read=false; this.filter_unread=true">Un-read</CButton>
        <CDropdown variant="input-group">
          <CDropdownToggle color="secondary" variant="outline">Action</CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem @click="markAll('mark_unread')"><font-awesome-icon icon='book' />Mark Un-read</CDropdownItem>
            <CDropdownItem @click="markAll('mark_read')"><font-awesome-icon icon='book-open' />Mark read</CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </CInputGroup>
    </CRow>
    <CRow>
      <template v-for="comic in filteredComics" :key="comic.selector" >
        <comic-card :data="comic" @updateComicList="updateComicList" @markPreviousRead="markPreviousRead" />
      </template>
    </CRow>
  </CContainer>
</template>

<script>
import {CContainer, CRow, CInputGroup, CFormInput, CButton, CDropdown, CDropdownToggle, CDropdownMenu,
  CDropdownItem} from "@coreui/vue"
import ComicCard from "@/components/ComicCard";
import api from '@/api'
import TheBreadcrumbs from "@/components/TheBreadcrumbs";

export default {
  name: "TheComicList",
  components: {TheBreadcrumbs, CRow, ComicCard, CContainer, CInputGroup, CFormInput, CButton, CDropdown,
    CDropdownToggle, CDropdownMenu, CDropdownItem},
  data () {
    return {
      comics: [],
      breadcrumbs: [
        {id: 0, selector: '', name: 'Home'}
      ],
      search_string: '',
      filter_read: false,
      filter_unread: false
  }},
  props: {
    selector: String
  },
  methods: {
    updateComicList () {
      let comic_list_url = this.$store.state.base_url + '/api/browse/'
      if (this.selector) {
        comic_list_url += this.selector + '/'
      }
      api.get(comic_list_url)
      .then(response => {
        this.comics = response.data
      })
      .catch((error) => {console.log(error)})
    },
    markPreviousRead (selector) {
      let selectors = []
      this.comics.every((item) => {
        if (item.selector === selector) {
          selectors.push(item.selector)
          return false
        } else {
          if (item.type === 'ComicBook') {
            selectors.push(item.selector)
          }
          return true
        }
      })
      let payload = { selectors: selectors }
      api.put('/api/action/mark_read/', payload).then(() => {
        this.updateComicList()
      })
    },
    markAll (action) {
      let selectors = []
      this.comics.filter(item => item.type === 'ComicBook').forEach((item) => {selectors.push(item.selector)})
      let payload = { selectors: selectors }
      api.put('/api/action/' + action + '/', payload).then(() => {
        this.updateComicList()
      })
    }
  },
  computed: {
    filteredComics() {
      let filtered_comics = [...this.comics]
      if (this.search_string) {
        filtered_comics = filtered_comics.filter(comic => {
          return comic.title.toLowerCase().includes(this.search_string.toLowerCase()) })
      }
      if (this.filter_read) {
        filtered_comics = filtered_comics.filter(comic => comic.finished )
      }
      if (this.filter_unread) {
        filtered_comics = filtered_comics.filter(comic => comic.unread )
      }
      return filtered_comics
    }
  },
  mounted () {
    this.updateComicList()
  },
  watch: {
    selector() {
      this.updateComicList()
    }
  }
}
</script>

<style scoped>
.dropdown-item {
  cursor: pointer;
}
</style>