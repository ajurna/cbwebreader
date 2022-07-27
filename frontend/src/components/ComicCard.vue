<template>
  <CCard class="col-xl-2 col-lg-2 col-md-3 col-sm-4 p-0 m-1 ">
    <CCardImage orientation="top" :src="thumbnail" @click="console.log('click')"/>
    <CCardBody class="pb-0 pt-0 pl-1 pr-1 card-img-overlay d-flex">
      <span class="badge rounded-pill bg-primary unread-badge" v-if="this.unread > 0 && data.type === 'Directory'">{{ this.unread }}</span>
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
        <CButton color="primary" @click="updateComic('mark_unread')" ><font-awesome-icon icon='book' /></CButton>
        <CButton color="primary" @click="updateComic('mark_read')" ><font-awesome-icon icon='book-open' /></CButton>
        <CDropdown variant="btn-group">
          <CDropdownToggle color="primary"><font-awesome-icon icon='edit' /></CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem @click="updateComic('mark_unread')"><font-awesome-icon icon='book' />Mark Un-read</CDropdownItem>
            <CDropdownItem @click="updateComic('mark_read')"><font-awesome-icon icon='book-open' />Mark read</CDropdownItem>
            <CDropdownItem v-if="data.type === 'ComicBook'" @click="$emit('markPreviousRead', data.selector)"><font-awesome-icon icon='book' /><font-awesome-icon icon='turn-up' />Mark previous comics read</CDropdownItem>
            <CDropdownItem v-if="data.type === 'Directory'"><font-awesome-icon icon='edit' />Edit comic</CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </CButtonGroup>
    </CCardFooter>
  </CCard>
</template>

<script>
import {CCard, CCardImage, CCardBody, CCardTitle, CCardText, CButton, CProgress, CProgressBar, CButtonGroup, CDropdown,
  CDropdownToggle, CDropdownMenu, CDropdownItem, CCardFooter} from '@coreui/vue'
import {useToast} from "vue-toast-notification";
import api from "@/api";

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
      api.get('/api/generate_thumbnail/' + this.data.selector + '/')
        .then((response) => {
          if (response.data.thumbnail) {
            this.thumbnail = response.data.thumbnail
            this.data.thumbnail = response.data.thumbnail
          }
        }).catch(() => {
          useToast().error('Error Generating Thumbnail: ' + this.data.title, {position:'top'});
        })
    },
    updateComic(action){
      let payload = { selectors: [this.data.selector] }
      api.put('/api/action/' + action +'/', payload).then(() => {
        this.$emit('updateComicList')
      }).catch(() => {
        useToast().error('action: ' + action + ' Failed', {position:'top'});
      })
    },
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
  beforeUpdate() {
    this.progress = this.data.progress / this.data.total * 100
    this.unread = this.data.total - this.data.progress
  }
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
.dropdown-item {
  cursor: pointer;
}
</style>