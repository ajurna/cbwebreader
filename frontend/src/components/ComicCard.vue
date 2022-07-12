<template>
  <CCard class="col-lg-2">
    <CCardImage orientation="top" :src="thumbnail"/>
    <CCardBody>
      <CCardTitle><a :href="url">{{ data.title }}</a></CCardTitle>
      <CCardText>
        <p class="text-center">{{data.progress}} / {{data.total}}</p>
        <CProgress class="mb-3">
          <CProgressBar :value="data.progress/data.total*100"/>
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
      </CCardText>

    </CCardBody>
  </CCard>
</template>

<script>
import {CCard, CCardImage, CCardBody, CCardTitle, CCardText, CButton, CProgress, CProgressBar, CButtonGroup, CDropdown,
  CDropdownToggle, CDropdownMenu, CDropdownItem} from '@coreui/vue'
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
    CDropdownItem
  },
  props: {
    data: Object
  },
  computed: {
    url() {
      return (this.data.type === 'Directory' ? '/browse/' + this.data.selector + '/' : '/comic/' + this.data.selector + '/');
    },
    thumbnail() {
      // return '/comic/' + data.selector + '/thumb/'
      return '/logo.png'
    }
  }
}
</script>

<style scoped>

</style>