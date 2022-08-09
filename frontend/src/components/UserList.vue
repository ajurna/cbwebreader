<template xmlns="">
  <CTable striped bordered>
    <CTableHead>
      <CTableRow>
        <CTableHeaderCell scope="col">#</CTableHeaderCell>
        <CTableHeaderCell scope="col">Username</CTableHeaderCell>
        <CTableHeaderCell scope="col">Email</CTableHeaderCell>
        <CTableHeaderCell scope="col">Superuser</CTableHeaderCell>
        <CTableHeaderCell scope="col">Classification</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <template v-for="(item, index) in users" :key="item.id">
        <CTableRow>
          <CTableHeaderCell scope="row">{{ item.id }}</CTableHeaderCell>
          <CTableDataCell class="">
            <router-link :to="{'name': 'user', params: { userid: item.id }}">{{ item.username }}</router-link>
          </CTableDataCell>
          <CTableDataCell>{{ item.email }}</CTableDataCell>
          <CTableDataCell>{{ item.is_superuser }}</CTableDataCell>
          <CTableDataCell>{{ this.$store.state.classifications.find(i => i.value === item.usermisc.toString()).label }}</CTableDataCell>
        </CTableRow>
      </template>
    </CTableBody>
  </CTable>
</template>

<script>
export default {
  name: "UserList",
  props: {
    users: Object
  }
}
</script>

<style scoped>

</style>