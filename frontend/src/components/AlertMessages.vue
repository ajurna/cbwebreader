<template>
  <div class="alert alert-dismissible fade show" :class="'alert-'+message.color" role="alert" v-for="message in messages" :key="message.text">
    {{message.text}}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" @click="this.$emit('removeMessage', message)"></button>
  </div>
</template>

<script>
export default {
  name: "AlertMessages",
  data() {
    return {
    }
  },
  props: {
    messages: Array
  },
  emits: ['removeMessage']
}
</script>

<style scoped>

</style>
