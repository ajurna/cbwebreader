<template>
  <CAlert :color="message.color" dismissible  v-for="message in messages" :key="message.text">
    {{message.text}}
  </CAlert>
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