<template>
  <CAlert :color="message.color" dismissible  v-for="message in messages">
    {{message.text}}
  </CAlert>
</template>

<script>
export default {
  name: "Messages",
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