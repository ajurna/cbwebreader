<template>
  <the-breadcrumbs :selector="selector"/>
  <the-comic-list :selector="selector" :key="selector" />
</template>

<script>
import TheComicList from "@/components/TheComicList";
import TheBreadcrumbs from "@/components/TheBreadcrumbs";

export default {
  name: 'BrowseView',
  components: {
    TheBreadcrumbs,
    TheComicList,
  },
  props: {
    selector: String
  }
}
</script>
