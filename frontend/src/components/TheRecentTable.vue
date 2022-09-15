<template>
  <div class="container">
    <div class="row">
      <div class="col d-flex align-items-center">
        <form class="form-inline ">
          <label class="my-1 px-1" for="selectChoices">Show</label>
          <select class="custom-select my-1 mr-sm-2 " id="selectChoices" v-model="this.page_size" @change="this.setPage(this.page)">
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
          <label class="my-1 px-1" for="selectChoices">entries</label>
        </form>
      </div>
      <div class="col d-flex justify-content-end">
        <form class="form-inline">
          <div class="form-floating">
            <input type="text" class="form-control" id="floatingInput" placeholder="name@example.com" v-model="search_text" @keyup="this.debounceInput()">
            <label for="floatingInput">Search</label>
          </div>
        </form>
      </div>
    </div>
    <div class="row">
      <caption>
        <h2>Recent Comics - <a :href="'/feed/' + this.feed_id + '/'">Feed</a></h2>
        Mark selected issues as:
        <select class="form-select-sm" name="func" id="func_selector" @change="this.performFunction()" v-model="func_selected">
          <option value="choose">Choose...</option>
          <option value="mark_read">Read</option>
          <option value="mark_unread">Un-Read</option>
        </select>
      </caption>
    </div>
    <div class="row">
      <table class="table table-striped table-bordered">
        <caption>Recent Comics</caption>
        <thead>
          <tr>
            <th scope="col"><input class="form-check-input m-0 position-relative mt-1" type="checkbox" value="" ref="select-all"></th>
            <th scope="col"></th>
            <th scope="col">Comic</th>
            <th scope="col">Date Added</th>
            <th scope="col">status</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="item in comics" :key="item.id">
            <tr>
              <th scope="row"><input ref="comic_selector" class="form-check-input m-0 position-relative mt-1" type="checkbox" :value="item.selector"></th>
              <td class=""><font-awesome-icon icon='book' class="" /></td>
              <td><router-link :to="{name: 'read', params: { selector: item.selector }}" class="" >{{ item.file_name }}</router-link></td>
              <td>{{ timeago(item.date_added) }}</td>
              <td>{{ get_status(item) }}</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div class="row">
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
import api from "@/api";
import * as timeago from 'timeago.js';
import Paginate from "vuejs-paginate-next";

export default {
  name: "TheRecentTable",
  components: {
    Paginate
  },
  data () {
    return {
      page: 1,
      page_size: 10,
      page_count: 1,
      search_text: '',
      comics: [],
      timeout: null,
      func_selected: 'choose',
      feed_id: ''
  }},
  computed: {
  },
  methods: {
    updateComicList () {
      let comic_list_url = '/api/recent/'
      let params = { params: { page: this.page, page_size: this.page_size } }

      if (this.search_text) {
        params.params.search_text = this.search_text
      }

      api.get(comic_list_url, params)
      .then(response => {
        this.comics = response.data.results
        this.page_count = Math.ceil(response.data.count / this.page_size)
      })
      .catch((error) => {
        if (error.response.data.detail === 'Invalid page.') {
          this.setPage(1)
        } else {
          console.log(error)
        }
      })
    },
    timeago(input) {
      return timeago.format(input)
    },
    get_status(item) {
      if (item.unread || item.unread === null) {
        return "Unread"
      } else if (item.finished) {
        return "Finished"
      } else {
        return item.last_read_page + ' / ' + item.page_count
      }
    },
    setPage(page) {
      this.page = page
      this.updateComicList()
    },
    debounceInput() {
      clearTimeout(this.timeout)
      this.timeout = setTimeout(() => {
        this.setPage(this.page)
      }, 500)
    },
    performFunction() {
      let selected_ids = []
      this.$refs.comic_selector.forEach((selector) => {
        if (selector.checked){
          selected_ids.push(selector.value)
        }
      })
      if (this.func_selected === 'mark_read') {
        let comic_mark_read = '/api/action/mark_read/'
        const payload = { selectors: selected_ids }
        api.put(comic_mark_read, payload).then(() => {
          this.updateComicList()
          this.func_selected = "choose"
        })
      } else if (this.func_selected === 'mark_unread') {
        let comic_mark_unread = '/api/action/mark_unread/'
        const payload = { selectors: selected_ids }
        api.put(comic_mark_unread, payload).then(() => {
          this.updateComicList()
          this.func_selected = "choose"
        })
      } else {
        this.func_selected = 'choose'
      }
    }
  },
  mounted() {
    this.updateComicList()
    let comic_mark_unread = '/api/account/feed_id/'
    api.get(comic_mark_unread).then((response) => {
      this.feed_id = response.data.feed_id
    })
  },
}
</script>

<style scoped>
.pagination {
  cursor: pointer;
}
</style>
