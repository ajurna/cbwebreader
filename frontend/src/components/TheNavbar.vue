<template>
  <CNavbar expand="lg" color-scheme="light" class="bg-light">
    <CContainer fluid>
      <CNavbarBrand href="#">Navbar</CNavbarBrand>
      <CNavbarToggler @click="visible = !visible"/>
      <CCollapse class="navbar-collapse" :visible="visible">
        <CNavbarNav>
          <CNavItem>
            <router-link :to="{name: 'home'}" class="nav-link" >Browse</router-link>
          </CNavItem>
          <CNavItem>
            <router-link :to="{name: 'recent'}" class="nav-link" >Recent</router-link>
          </CNavItem>
          <CNavItem>
            <CNavLink href="#">Account</CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink href="#">Users</CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink href="#">Log Out</CNavLink>
          </CNavItem>
        </CNavbarNav>
      </CCollapse>
    </CContainer>
  </CNavbar>
</template>
<script>
import { CNavbar, CNavbarNav, CContainer, CNavbarBrand, CNavbarToggler, CCollapse, CNavItem, CNavLink } from '@coreui/vue'
export default {
  name: "TheNavbar",
  components: {
    CNavbar,
    CNavbarNav,
    CContainer,
    CNavbarBrand,
    CNavbarToggler,
    CCollapse,
    CNavItem,
    CNavLink
  },
  data() {
    return {
      visible: true
    }
  }
}
</script>

<style scoped>

</style>