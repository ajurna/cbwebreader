<template>
  <CCard class="col-lg-2">
    <CCardImage orientation="top" :src="thumbnail" />
    <CCardBody class="pb-0 pt-0">
      <CCardTitle>
        <router-link :to="(data.type === 'Directory' ? {'name': 'browse', params: { selector: data.selector }} : {'name': 'read', params: { selector: data.selector }})">{{ data.title }}</router-link>
      </CCardTitle>
    </CCardBody>
    <CCardFooter class="pl-0 pr-0 pt-0">
      <CProgress class="mb-1 position-relative" >
        <CProgressBar :value="data.progress/data.total*100" />
        <small class="justify-content-center d-flex position-absolute w-100 h-100" style="line-height: normal">{{data.progress}} / {{data.total}}</small>
      </CProgress>
      <CButtonGroup class="w-100">
        <CButton color="primary"><font-awesome-icon icon='book' /> </CButton>
        <CButton color="primary"><font-awesome-icon icon='book-open' /> </CButton>
        <CDropdown variant="btn-group">
          <CDropdownToggle color="primary"><font-awesome-icon icon='edit' /></CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem href="#"><font-awesome-icon icon='book' /> Mark Un-read</CDropdownItem>
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
      thumbnail: '/static/img/placeholder.png'
    }},
  methods: {
    updateThumbnail () {
      api.get(this.$store.state.base_url + '/api/generate_thumbnail/' + this.data.selector + '/')
        .then((response) => {this.thumbnail = response.data.thumbnail})
        .catch(() => {})
    }
  },
  mounted () {
    if (this.data.thumbnail) {
      this.thumbnail = this.data.thumbnail
    } else {
      this.updateThumbnail()
    }

  },
}
</script>

<style scoped>

</style>