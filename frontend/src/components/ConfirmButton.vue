<template>
  <div class="btn-group" role="group" aria-label="Basic example">
    <button type="button" class="btn" :class="'btn-'+color" v-if="!confirm" @click="confirm = !confirm">{{ label }}</button>
    <button type="button" class="btn btn-outline-success text-nowrap" v-if="confirm" @click="performAction">
      <font-awesome-icon icon="check" class="" />Yes
    </button>
    <button type="button" class="btn btn-outline-danger text-nowrap" v-if="confirm" @click="confirm = !confirm">
      <font-awesome-icon icon='times' class=""/>No
    </button>
  </div>
</template>
<script>
export default {
  name: 'confirm-button',
  data () {
    return {
      confirm: false,
    }
  },
  props: {
    label: String,
    color: {
      type: String,
      default: 'danger'
    },
    action: {}
  },
  methods: {
    performAction() {
      this.action()
      this.confirm = false
    }
  }
}
</script>
