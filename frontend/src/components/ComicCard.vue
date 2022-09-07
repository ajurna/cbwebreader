<template>
  <div class="col">
    <div class="card">
      <div class="card card-body p-0" @click="$router.push((data.type === 'Directory' ? {'name': 'browse', params: { selector: data.selector }} : {'name': 'read', params: { selector: data.selector }}))">
        <img :src="thumbnail" class="card-img-top" :alt="data.title">
        <span class="badge rounded-pill bg-primary unread-badge" v-if="this.unread > 0 && data.type === 'Directory'">{{ this.unread }}</span>
        <span class="badge rounded-pill bg-warning classification-badge" v-if="card_type === 'Directory'" >{{ this.$store.state.classifications.find(i => i.value === classification).label }}</span>
        <h5 class="card-title text-break mb-0">
          <router-link :to="(data.type === 'Directory' ? {'name': 'browse', params: { selector: data.selector }} : {'name': 'read', params: { selector: data.selector }})">{{ data.title }}</router-link>
        </h5>
      </div>
      <div class="card-footer px-0 pb-0">
        <div class="progress position-relative">
          <div class="progress-bar" role="progressbar" aria-label="Basic example" :style="'width: '+ progressPercentCalc +'%;'" :aria-valuenow="progressPercentCalc" aria-valuemin="0" aria-valuemax="100"></div>
          <small class="justify-content-center d-flex position-absolute w-100 h-100" style="line-height: normal">{{ progressCalc }} / {{data.total}}</small>
        </div>
        <div class="btn-group w-100 pt-1" role="group" aria-label="Basic example">
          <button type="button" class="btn btn-primary" @click="updateComic('mark_unread')"><font-awesome-icon icon='book' /></button>
          <button type="button" class="btn btn-primary" @click="updateComic('mark_read')" ><font-awesome-icon icon='book-open' /></button>
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-primary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
              <font-awesome-icon icon='edit' />
            </button>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" @click="updateComic('mark_unread')"><font-awesome-icon icon='book' /> Mark Un-read</a></li>
              <li><a class="dropdown-item" @click="updateComic('mark_read')"><font-awesome-icon icon='book-open' /> Mark read</a></li>
              <li><a class="dropdown-item" v-if="data.type === 'ComicBook'" @click="$emit('markPreviousRead', data.selector)"><font-awesome-icon icon='book' /><font-awesome-icon icon='turn-up' />Mark previous comics read</a></li>
              <li><a class="dropdown-item" v-if="data.type === 'Directory'" data-bs-toggle="modal" :data-bs-target="'#'+data.selector"><font-awesome-icon icon='edit' />Edit comic</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="modal fade" :id="data.selector" tabindex="-1" :aria-labelledby="data.selector+'-label'" aria-hidden="true" >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" :id="data.selector+'-label'">{{ data.title }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form @submit="updateDirectory">
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-check-label mb-1" :for="data.selector+'-classification'" >
                Classification
              </label>
              <select class="form-select" :id="data.selector+'-classification'" v-model="new_classification">
                <option v-for="class_options in [...this.$store.state.classifications]" :key="class_options.value" :value="class_options.value">{{class_options.label}}</option>
              </select>

            </div>
            <div class="mb-3">
              <input class="form-check-input" type="checkbox" value="" :id="data.selector+'-recursive'" v-model="recursive">
              <label class="form-check-label px-1" :for="data.selector+'-recursive'" >
                Recursive
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="submit" class="btn btn-primary" data-bs-dismiss="modal">Submit</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import {useToast} from "vue-toast-notification";
import api from "@/api";
import 'bootstrap/js/dist/modal'

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
  position: absolute;
  bottom: 0;
  left: 0;
  text-decoration: none;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85), transparent);
  width: 100%;
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
