<template>
  <div class="container" v-if="comics.length">
    <h4>Continue reading</h4>
    <div class="shelf">
      <router-link class="shelf-card" v-for="item in comics" :key="item.selector" :to="{ name: 'read', params: { selector: item.selector } }">
        <div class="thumb">
          <img :src="item.thumbnail" :alt="item.title" />
          <div class="bar"><div class="fill" :style="{ width: percent(item) }"></div></div>
        </div>
        <div class="meta">
          <div class="title">{{ item.title }}</div>
          <div class="sub" v-if="item.on_deck"><span class="badge">On deck</span></div>
          <div class="sub" v-else>{{ item.progress }} / {{ item.total }} · {{ timeago(item.last_read_time) }}</div>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script>
import api from '@/api'
import * as timeago from 'timeago.js'

export default {
  name: 'TheContinueReading',
  props: {
    selector: { type: String, default: '' }
  },
  data () {
    return {
      comics: []
    }
  },
  methods: {
    updateContinueReading () {
      const url = this.selector ? '/api/read/continue/?directory=' + this.selector : '/api/read/continue/'
      api.get(url)
        .then((response) => {
          this.comics = response.data
        })
    },
    percent (item) {
      return (item.total ? Math.round((item.progress / item.total) * 100) : 0) + '%'
    },
    timeago (input) {
      return timeago.format(input)
    }
  },
  mounted () {
    this.updateContinueReading()
  }
}
</script>

<style scoped>
.shelf {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  gap: 12px;
  padding-bottom: 8px;
}

.shelf-card {
  flex: 0 0 auto;
  width: 150px;
  color: inherit;
  text-decoration: none;
}

.thumb {
  position: relative;
}

.thumb img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 4px;
  background: #e9ecef;
}

.bar {
  height: 4px;
  margin-top: 4px;
  background: rgba(0, 0, 0, 0.2);
}

.bar .fill {
  height: 100%;
  background: #007bff;
}

.meta {
  padding-top: 4px;
  font-size: 0.9rem;
}

.title {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.sub {
  font-size: 0.8rem;
  color: #6c757d;
}

.badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 3px;
  background: #007bff;
  color: #fff;
  font-size: 0.75rem;
}
</style>
