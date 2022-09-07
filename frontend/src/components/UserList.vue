<template>
  <table class="table table-striped table-bordered">
    <caption>User list</caption>
    <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Username</th>
        <th scope="col">Email</th>
        <th scope="col">Superuser</th>
        <th scope="col">Classification</th>
      </tr>
    </thead>
    <tbody>
      <template v-for="item in users" :key="item.id">
        <tr>
          <th scope="row">{{ item.id }}</th>
          <td class="">
            <router-link :to="{'name': 'user', params: { userid: item.id }}">{{ item.username }}</router-link>
          </td>
          <td>{{ item.email }}</td>
          <td>{{ item.is_superuser }}</td>
          <td>{{ this.$store.state.classifications.find(i => i.value === item.classification.toString()).label }}</td>
        </tr>
      </template>
    </tbody>
  </table>
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
