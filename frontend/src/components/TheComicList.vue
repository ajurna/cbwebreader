<template>
  <div class="container-fluid">
    <div class="row">
      <div class="input-group">
        <input class="form-control" aria-label="Filter comics by name" placeholder="Search" v-model="this.filters.search_string" @input="queueUpdate">
        <button type="button" class="btn" :class="(!filters.filter_read && !filters.filter_unread? 'btn-outline-primary' : 'btn-outline-secondary')" @click="setFilter(null)">All</button>
        <button type="button" class="btn" :class="(filters.filter_read && !filters.filter_unread? 'btn-outline-primary' : 'btn-outline-secondary')" @click="setFilter('read')">Read</button>
        <button type="button" class="btn" :class="(!filters.filter_read && filters.filter_unread? 'btn-outline-primary' : 'btn-outline-secondary')" @click="setFilter('unread')">Un-read</button>
        <button type="button" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">Action</button>
        <ul class="dropdown-menu">
          <li><a class="dropdown-item" @click="markAll('mark_unread')"><font-awesome-icon icon='book' />Mark Un-read</a></li>
          <li><a class="dropdown-item" @click="markAll('mark_read')"><font-awesome-icon icon='book-open' />Mark read</a></li>
        </ul>
        <button type="button" class="btn btn-outline-secondary" :disabled="scanning" title="Read this folder from disk again" @click="scanFolder">
          <font-awesome-icon icon='refresh' />{{ scanning ? 'Scanning…' : 'Scan' }}
        </button>
      </div>
    </div>
    <div class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-6 row-cols-xl-auto mt-1" >
      <template v-if="loading">
        <div class="col-12 col-xl-12 col-lg-12 col-md-12 col-sm-12 col-xs-12">
          <div class="progress mt-3">
            <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" role="progressbar" aria-label="Loading data" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div>
          </div>
        </div>
      </template>
      <template v-else>
        <template v-for="comic in comics" :key="comic.selector" >
          <comic-card :data="comic" @updateComicList="updateComicList" @markPreviousRead="markPreviousRead" @updateThumbnail="updateThumbnail" />
        </template>
      </template>
    </div>
    <div class="row" v-if="page_count > 1">
      <div class="col">
        Showing page {{ this.page }} of {{ this.page_count }} pages.
      </div>
      <div class="col d-flex justify-content-end">
        <paginate
          v-model="this.page"
          :page-count="this.page_count"
          :click-handler="this.setPage"
          :prev-text="'Prev'"
          :next-text="'Next'"
          :container-class="'pagination '"
        >
        </paginate>
      </div>
    </div>
  </div>
</template>

<script>
import ComicCard from "@/components/ComicCard";
import Paginate from "vuejs-paginate-next";
import api from '@/api'
import store from "@/store";

export default {
  name: "TheComicList",
  components: {ComicCard, Paginate},
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
      page: 1,
      page_size: 10,
      page_count: 1,
      loading: true,
      scanning: false,
      timeout: null
  }},
  props: {
    selector: String
  },
  methods: {
    filter_id () {
      return this.selector ? this.selector : 'home'
    },
    updateComicList () {
      this.loading = true
      let comic_list_url = '/api/browse/'
      if (this.selector) {
        comic_list_url += this.selector + '/'
      }
      let params = { params: { page: this.page, page_size: this.page_size } }
      if (this.filters.search_string) {
        params.params.search = this.filters.search_string
      }
      if (this.filters.filter_read) {
        params.params.read = 'true'
      } else if (this.filters.filter_unread) {
        params.params.read = 'false'
      }
      api.get(comic_list_url, params)
      .then(response => {
        this.comics = response.data.results
        this.page_count = Math.ceil(response.data.count / this.page_size)
        this.loading = false
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.detail === 'Invalid page.') {
          this.setPage(1)
        } else {
          console.log(error)
        }
        this.loading = false
      })
    },
    // Search and the read/unread buttons now filter on the server, so the pager count
    // matches what is shown. Debounce so typing does not send one request per keystroke.
    queueUpdate () {
      clearTimeout(this.timeout)
      this.timeout = setTimeout(() => this.updateComicList(), 500)
    },
    setFilter (which) {
      this.filters.filter_read = which === 'read'
      this.filters.filter_unread = which === 'unread'
      this.page = 1
      this.queueUpdate()
    },
    setPage (page) {
      this.page = page
      this.updateComicList()
    },
    scanFolder () {
      this.scanning = true
      api.post('/api/browse/scan/', { selector: this.selector || null })
        .then(response => {
          this.comics = response.data.results
          this.page_count = Math.ceil(response.data.count / this.page_size)
          this.scanning = false
        })
        .catch((error) => {
          console.log(error)
          this.scanning = false
        })
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
      // Only the page that is on screen, because that is what the user can see.
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
  mounted () {
    let filter_id = this.filter_id()
    if (!(filter_id in store.state.filters)) {
      store.state.filters[filter_id] = this.filters
    } else {
      this.filters = store.state.filters[filter_id]
    }
    this.updateComicList()
  },
  beforeUnmount () {
    clearTimeout(this.timeout)
  },
  watch: {
    filters() {
      store.state.filters[this.filter_id()] = this.filters
    }
  },
}
</script>

<style scoped>
.dropdown-item {
  cursor: pointer;
}
</style>
