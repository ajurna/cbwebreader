<template>
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
      <template v-for="(item, index) in comics" :key="item.id">
        <CTableRow>
          <CTableHeaderCell scope="row"><input ref="comic_selector" class="form-check-input m-0 position-relative mt-1" type="checkbox" :value="item.selector"></CTableHeaderCell>
          <CTableDataCell class=""><font-awesome-icon icon='book' class="" /></CTableDataCell>
          <CTableDataCell><router-link :to="{name: 'read', params: { selector: item.selector }}" class="" >{{ item.file_name }}</router-link></CTableDataCell>
          <CTableDataCell>{{ timeago(item.date_added) }}</CTableDataCell>
          <CTableDataCell>{{ get_status(item) }}</CTableDataCell>
        </CTableRow>
      </template>
    </CTableBody>
  </CTable>
</template>

<script>
import {CTable, CTableHead, CTableBody, CTableRow, CTableHeaderCell, CTableDataCell} from "@coreui/vue";
export default {
  name: "UserList",
  components: {CTable, CTableHead, CTableBody, CTableRow, CTableHeaderCell, CTableDataCell}
}
</script>

<style scoped>

</style>