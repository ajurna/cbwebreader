<template>
  <CContainer>
    <CRow>
      <CInputGroup>
        <CFormInput placeholder="Search" aria-label="Filter comics by name" v-model="this.filters.search_string"/>
        <CButton type="button" :color="(!filters.filter_read && !filters.filter_unread? 'primary' : 'secondary')" variant="outline" @click="filters.filter_read=false; filters.filter_unread=false">All</CButton>
        <CButton type="button" :color="(filters.filter_read && !filters.filter_unread? 'primary' : 'secondary')" variant="outline" @click="filters.filter_read=true; filters.filter_unread=false">Read</CButton>
        <CButton type="button" :color="(!filters.filter_read && filters.filter_unread? 'primary' : 'secondary')" variant="outline" @click="filters.filter_read=false; filters.filter_unread=true">Un-read</CButton>
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
      <template v-for="comic in filteredComics" :key="comic.selector" v-if="!loading">
        <comic-card :data="comic" @updateComicList="updateComicList" @markPreviousRead="markPreviousRead" @updateThumbnail="updateThumbnail" />
      </template>
      <CCol v-if="loading">
        <CProgress class="mt-3" >
          <CProgressBar color="success" variant="striped" animated  :value="100"/>
        </CProgress>
      </CCol>
    </CRow>
  </CContainer>
</template>

<script>
import ComicCard from "@/components/ComicCard";
import api from '@/api'
import store from "@/store";

export default {
  name: "TheComicList",
  components: {ComicCard},
  data () {
    return {
      comics: [],
      breadcrumbs: [
        {id: 0, selector: '', name: 'Home'}
      ],
      filters: {
        search_string: '',
        filter_read: false,
        filter_unread: false
      },
      loading: true
  }},
  props: {
    selector: String
  },
  methods: {
    updateComicList () {
      this.loading = true
      let comic_list_url = '/api/browse/'
      if (this.selector) {
        comic_list_url += this.selector + '/'
      }
      api.get(comic_list_url)
      .then(response => {
        this.comics = response.data
        this.loading = false
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
    },
    updateThumbnail(resp){
      this.comics.find(i => i.selector === resp.selector).thumbnail = resp.thumbnail
    }
  },
  computed: {
    filteredComics() {
      let filtered_comics = [...this.comics]
      if (this.filters.search_string) {
        filtered_comics = filtered_comics.filter(comic => {
          return comic.title.toLowerCase().includes(this.filters.search_string.toLowerCase()) })
      }
      if (this.filters.filter_read) {
        filtered_comics = filtered_comics.filter(comic => comic.finished )
      }
      if (this.filters.filter_unread) {
        filtered_comics = filtered_comics.filter(comic => comic.unread )
      }
      return filtered_comics
    }
  },
  mounted () {
    this.updateComicList()
  },
  beforeUpdate() {
    let filter_id = ( this.selector ? this.selector : 'home')
    if (filter_id in store.state.filters) {
      this.filters = store.state.filters[filter_id]
    } else {
      this.filters = {
        search_string: '',
        filter_read: false,
        filter_unread: false
      }
      store.state.filters[filter_id] = this.filters
    }
  },
  watch: {
    filters() {
      let filter_id = ( this.selector ? this.selector : 'home')
      store.state.filters[filter_id] = this.filters
    }
  },
}
</script>

<style scoped>
.dropdown-item {
  cursor: pointer;
}
</style>