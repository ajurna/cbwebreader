<template>
  <div class="container-fluid">
    <div class="row">
      <div class="input-group">
        <input class="form-control" aria-label="Filter comics by name" placeholder="Search" v-model="this.filters.search_string">
        <button type="button" class="btn" :class="(!filters.filter_read && !filters.filter_unread? 'btn-outline-primary' : 'btn-outline-secondary')" @click="filters.filter_read=false; filters.filter_unread=false">All</button>
        <button type="button" class="btn" :class="(filters.filter_read && !filters.filter_unread? 'btn-outline-primary' : 'btn-outline-secondary')" @click="filters.filter_read=true; filters.filter_unread=false">Read</button>
        <button type="button" class="btn" :class="(!filters.filter_read && filters.filter_unread? 'btn-outline-primary' : 'btn-outline-secondary')" @click="filters.filter_read=false; filters.filter_unread=true">Un-read</button>
        <button type="button" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">Action</button>
        <ul class="dropdown-menu">
          <li><a class="dropdown-item" @click="markAll('mark_unread')"><font-awesome-icon icon='book' />Mark Un-read</a></li>
          <li><a class="dropdown-item" @click="markAll('mark_read')"><font-awesome-icon icon='book-open' />Mark read</a></li>
        </ul>
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
        <template v-for="comic in filteredComics" :key="comic.selector" >
          <comic-card :data="comic" @updateComicList="updateComicList" @markPreviousRead="markPreviousRead" @updateThumbnail="updateThumbnail" />
        </template>
      </template>
    </div>
  </div>
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
