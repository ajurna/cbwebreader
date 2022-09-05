<template>
  <div class="alert alert-dismissible fade show" :class="'alert-'+message.color" role="alert" v-for="message in messages" :key="message.text">
    {{message.text}}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
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
  }
}
</script>

<style scoped>

</style>
