<template>
  <CCard class="col-xl-2 col-lg-2 col-md-3 col-sm-4 p-0 m-1 ">
    <CCardImage orientation="top" :src="thumbnail" @click="console.log('click')"/>
    <CCardBody class="pb-0 pt-0 pl-1 pr-1 card-img-overlay d-flex">
      <span class="badge rounded-pill bg-primary unread-badge" v-if="this.unread > 0">{{ this.unread }}</span>
      <CCardTitle class="align-self-end pb-5 mb-4 text-break" style="">
        <router-link :to="(data.type === 'Directory' ? {'name': 'browse', params: { selector: data.selector }} : {'name': 'read', params: { selector: data.selector }})">{{ data.title }}</router-link>
      </CCardTitle>
    </CCardBody>
    <CCardFooter class="pl-0 pr-0 pt-0">
      <CProgress class="mb-1 position-relative" >
        <CProgressBar :value="this.progress" />
        <small class="justify-content-center d-flex position-absolute w-100 h-100" style="line-height: normal">{{data.progress}} / {{data.total}}</small>
      </CProgress>
      <CButtonGroup class="w-100">
        <CButton color="primary"><font-awesome-icon icon='book' /></CButton>
        <CButton color="primary"><font-awesome-icon icon='book-open' /></CButton>
        <CDropdown variant="btn-group">
          <CDropdownToggle color="primary"><font-awesome-icon icon='edit' /></CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem href="#"><font-awesome-icon icon='book' />Mark Un-read</CDropdownItem>
            <CDropdownItem href="#"><font-awesome-icon icon='book-open' />Mark read</CDropdownItem>
            <CDropdownItem href="#"><font-awesome-icon icon='edit' />Edit Comic</CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </CButtonGroup>
    </CCardFooter>
  </CCard>
</template>

<script>
import {CCard, CCardImage, CCardBody, CCardTitle, CCardText, CButton, CProgress, CProgressBar, CButtonGroup, CDropdown,
  CDropdownToggle, CDropdownMenu, CDropdownItem, CCardFooter} from '@coreui/vue'
import api from '@/api'
export default {
  name: "ComicCard",
  components: {
    CCard,
    CCardImage,
    CCardBody,
    CCardTitle,
    CCardText,
    CButton,
    CProgress,
    CProgressBar,
    CButtonGroup,
    CDropdown,
    CDropdownToggle,
    CDropdownMenu,
    CDropdownItem,
    CCardFooter
  },
  props: {
    data: Object
  },
  data () {
    return {
      thumbnail: '/static/img/placeholder.png',
      unread: 0,
      progress: 0
    }},
  methods: {
    updateThumbnail () {
      api.get(this.$store.state.base_url + '/api/generate_thumbnail/' + this.data.selector + '/')
        .then((response) => {
          if (response.data.thumbnail) {
            this.thumbnail = response.data.thumbnail
            this.data.thumbnail = response.data.thumbnail
          }

        })
        .catch(() => {})
    }
  },
  mounted () {
    if (this.data.thumbnail) {
      this.thumbnail = this.data.thumbnail
    } else {
      this.updateThumbnail()
    }
    this.unread = this.data.total - this.data.progress
    this.progress = this.data.progress / this.data.total * 100
  },
}
</script>

<style scoped>
.card-title a {
  color: white;
  text-shadow: .2rem .2rem .3rem black ;
  }
.card .unread-badge {
    position: absolute;
    top: 10px;
    left: 10px;
    padding: 5px;
    color: #fff;
}
</style>