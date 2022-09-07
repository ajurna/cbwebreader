<template>
  <ul class="list-group list-group-horizontal">
    <li class="list-group-item" @click="this.$emit('prevComic')">Prev&nbsp;Comic</li>
    <li class="list-group-item" @click="prevPage">Prev</li>
    <template v-for="ind in visible_pages" :key="ind">
      <li class="list-group-item" :class="(ind===modelValue ? 'list-group-item-primary': '')" @click="setPage(ind)">{{ ind }}</li>
    </template>
    <li class="list-group-item" @click="nextPage">Next</li>
    <li class="list-group-item" @click="this.$emit('nextComic')">Next&nbsp;Comic</li>
  </ul>
</template>

<script>
export default {
  name: "ComicPaginate",
  props: {
    page_count: Number,
    modelValue: Number,
  },
  emits: ['update:modelValue', 'setPage', 'prevComic', 'nextComic'],
  methods: {
    setPage(evt){
      if (evt !== '...'){
        this.$emit('setPage', evt)
      }
    },
    nextPage(){
      if (this.modelValue === this.page_count){
        this.$emit('nextComic')
      } else {
        this.setPage(this.modelValue + 1)
      }
    },
    prevPage(){
      if (this.modelValue === 1){
        this.$emit('prevComic')
      } else {
        this.setPage(this.modelValue - 1)
      }
    }
  },
  computed: {
    visible_pages(){
      let out = []
      if (this.page_count <= 5){
        for (let i = 1; i <= this.page_count; i++){
          out.push(i)
        }
        return out
      }

      let min = Math.max(1, this.modelValue - 2)
      let max = Math.min(this.page_count, this.modelValue + 2)

      for (let i = min; i <= max; i++){
        out.push(i)
      }

      if (out[0] !== 1){
        out.splice(0, 1, ...[1, '...'])
      }
      if (out[out.length - 1] !==this.page_count){
        out.splice(out.length - 1,1, ...['...', this.page_count])
      }
      return out
    }
  }
}
</script>

<style scoped>

</style>
