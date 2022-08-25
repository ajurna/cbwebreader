<template>
  <CButtonGroup>
    <CButton :color="color" v-if="!confirm" @click="confirm = !confirm">{{ label }}</CButton>
    <CButton color="success" class="text-nowrap" v-if="confirm" variant="outline" @click="performAction">
      <font-awesome-icon icon='check' class=""/>
      Yes
    </CButton>
    <CButton color="danger" class="text-nowrap" v-if="confirm" variant="outline"
             @click="confirm = !confirm">
      <font-awesome-icon icon='times' class=""/>
      No
    </CButton>
  </CButtonGroup>
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
