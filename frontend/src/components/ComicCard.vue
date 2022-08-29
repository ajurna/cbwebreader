<template>
  <CCol>
    <CCard class="">
      <CCardImage orientation="top" :src="thumbnail"/>
      <CCardBody class="pb-0 pt-0 pl-1 pr-1 card-img-overlay d-flex" @click="$router.push((data.type === 'Directory' ? {'name': 'browse', params: { selector: data.selector }} : {'name': 'read', params: { selector: data.selector }}))">
        <span class="badge rounded-pill bg-primary unread-badge" v-if="this.unread > 0 && data.type === 'Directory'">{{ this.unread }}</span>
        <span class="badge rounded-pill bg-warning classification-badge" v-if="card_type === 'Directory'" >{{ this.$store.state.classifications.find(i => i.value === classification).label }}</span>
        <CCardTitle class="align-self-end text-break" style="">
          <router-link :to="(data.type === 'Directory' ? {'name': 'browse', params: { selector: data.selector }} : {'name': 'read', params: { selector: data.selector }})">{{ data.title }}</router-link>
        </CCardTitle>
      </CCardBody>
      <CCardFooter class="pl-0 pr-0 pt-0">
        <CProgress class="mb-1 position-relative" >
          <CProgressBar :value="progressPercentCalc" />
          <small class="justify-content-center d-flex position-absolute w-100 h-100" style="line-height: normal">{{ progressCalc }} / {{data.total}}</small>
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
              <CDropdownItem v-if="data.type === 'Directory'" @click="editDirectoryVisible = true"><font-awesome-icon icon='edit' />Edit comic</CDropdownItem>
            </CDropdownMenu>
          </CDropdown>
        </CButtonGroup>
      </CCardFooter>
    </CCard>
    <CModal :visible="editDirectoryVisible" @close="editDirectoryVisible = false">
      <CModalHeader>
        <CModalTitle>{{ data.title }}</CModalTitle>
      </CModalHeader>
      <CForm @submit="updateDirectory">
        <CModalBody>
          <CFormSelect
            label="Classification"
            aria-label="Set Classification"
            v-model="new_classification"
            :options="[...this.$store.state.classifications]">
          </CFormSelect>
          <CFormCheck
            label="Recursive"
            class="mt-2"
            v-model="recursive"
          />
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" @click="editDirectoryVisible = false ">
            Close
          </CButton>
          <CButton color="primary" type="submit">Save changes</CButton>
        </CModalFooter>
      </CForm>
    </CModal>
  </CCol>
</template>

<script>
import {useToast} from "vue-toast-notification";
import api from "@/api";

export default {
  name: "ComicCard",
  components: {
  },
  props: {
    data: Object
  },
  data () {
    return {
      thumbnail: '/static/img/placeholder.png',
      unread: 0,
      progress: 0,
      classification: '0',
      new_classification: '0',
      card_type: '',
      editDirectoryVisible: false,
      recursive: true
    }},
  methods: {
    updateThumbnail () {
      api.get('/api/generate_thumbnail/' + this.data.selector + '/')
        .then((response) => {
          if (response.data.thumbnail) {
            this.$emit('updateThumbnail', response.data)
            this.thumbnail = response.data.thumbnail
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
    updateDirectory() {
      let payload = {
        selector: this.data.selector,
        classification: ~~this.new_classification
      }
      if (this.recursive){
        api.put('/api/directory/' + this.data.selector + '/', payload).then(response => {
          this.classification = response.data[0].classification.toString()
          useToast().success('Change classification of ' + this.data.title + ' to "' + this.$store.state.classifications.find(i => i.value === this.classification).label + '"', {position:'top'});
          this.editDirectoryVisible = false
        })
      } else {
        api.patch('/api/directory/' + this.data.selector + '/', payload).then(response => {
          this.classification = response.data.classification.toString()
          useToast().success('Change classification of ' + this.data.title + ' to "' + this.$store.state.classifications.find(i => i.value === this.classification).label + '"', {position:'top'});
          this.editDirectoryVisible = false
        })
      }

    }
  },
  mounted () {
    if (this.data.thumbnail) {
      this.thumbnail = this.data.thumbnail
    } else {
      this.updateThumbnail()
    }
    this.unread = this.data.total - this.data.progress
    this.classification = this.data.classification.toString()
    this.new_classification = this.classification
    this.card_type = this.data.type
  },
  beforeUpdate() {
    this.unread = this.data.total - this.data.progress
  },
  emits: ['updateComicList', 'markPreviousRead', 'updateThumbnail'],
  computed: {
    progressCalc () {
      if (this.data.type === 'ComicBook'){
        return (this.data.unread ? 0 : this.data.progress)
      } else {
        return this.data.progress
      }
    },
    progressPercentCalc () {
      if (this.data.type === 'ComicBook') {
        return (this.data.unread ? 0 : this.data.progress / this.data.total * 100)
      } else {
        return this.data.progress / this.data.total * 100
      }
    }
  }
}
</script>

<style scoped>

.card-title a {
  color: white;
  text-shadow: .2rem .2rem .3rem black ;
}

h5.card-title {
  margin-bottom: 75px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85), transparent);
}

h5.card-title::before {
  filter: blur(12px);
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
.card .classification-badge {
  position:absolute;
  top:10px;
  right: 10px;
  padding:5px;
  color:black;
}
</style>