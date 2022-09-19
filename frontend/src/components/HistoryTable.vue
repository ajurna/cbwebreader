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
        <h2>Reading History</h2>
      </caption>
    </div>
    <div class="row">
      <table class="table table-striped table-bordered">
        <caption>Recent Comics</caption>
        <thead>
          <tr>
            <th scope="col"></th>
            <th scope="col">Comic</th>
            <th scope="col">Date Read</th>
            <th scope="col">status</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="item in comics" :key="item.id">
            <tr>
              <th scope="row"><font-awesome-icon icon='book' class="" /></th>
              <td><router-link :to="{name: 'read', params: { selector: item.selector }}" class="" >{{ item.file_name }}</router-link></td>
              <td>{{ timeago(item.last_read_time) }}</td>
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
import Paginate from "vuejs-paginate-next";
import api from "@/api";
import * as timeago from "timeago.js";

export default {
  name: "HistoryTable",
  components: {
    Paginate
  },
  data () {
    return {
      page: 1,
      page_size: 10,
      page_count: 2,
      search_text: '',
      comics: [],
      timeout: null,
      func_selected: 'choose',
      feed_id: ''
  }},
  methods: {
    updateComicList () {
      let comic_list_url = '/api/history/'
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
  },
  mounted() {
    this.updateComicList()
  },
}
</script>

<style scoped>

</style>
