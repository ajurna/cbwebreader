<template>
  <CContainer>
    <CRow>
      <CInputGroup>
        <CFormInput placeholder="Search" aria-label="Filter comics by name" v-model="this.search_string"/>
        <CButton type="button" color="secondary" variant="outline" @click="this.filter_read=false; this.filter_unread=false">All</CButton>
        <CButton type="button" color="secondary" variant="outline" @click="this.filter_read=true; this.filter_unread=false">Read</CButton>
        <CButton type="button" color="secondary" variant="outline" @click="this.filter_read=false; this.filter_unread=true">Un-read</CButton>
        <CDropdown variant="input-group">
          <CDropdownToggle color="secondary" variant="outline">Action</CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem href="#"><font-awesome-icon icon='book' />Mark Un-read</CDropdownItem>
            <CDropdownItem href="#"><font-awesome-icon icon='book-open' />Mark read</CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </CInputGroup>
    </CRow>
    <CRow>
      <template v-for="comic in filteredComics" :key="comic.title" >
        <comic-card :data="comic" />
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
  },
  computed: {
    filteredComics() {
      let filtered_comics = [...this.comics]
      if (this.search_string) {
        filtered_comics = filtered_comics.filter(comic => {
          return comic.title.toLowerCase().includes(this.search_string.toLowerCase()) })
      }
      if (this.filter_read) {
        filtered_comics = filtered_comics.filter(comic => {
          return comic.unread })
      }
      if (this.filter_unread) {
        filtered_comics = filtered_comics.filter(comic => {
          return comic.finished })
      }
      return filtered_comics
    }
  },
  mounted () {
    this.updateComicList()
  },
  watch: {
    selector(oldSelector, newSelector) {
      this.updateComicList()
    }
  }
}
</script>

<style scoped>

</style>