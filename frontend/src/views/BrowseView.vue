<template>
  <the-breadcrumbs :selector="selector"/>
  <the-continue-reading :selector="selector" :key="selector" />
  <the-comic-list :selector="selector" :key="selector" />
</template>

<script>
import TheComicList from "@/components/TheComicList";
import TheContinueReading from "@/components/TheContinueReading";
import TheBreadcrumbs from "@/components/TheBreadcrumbs";

export default {
  name: 'BrowseView',
  components: {
    TheBreadcrumbs,
    TheContinueReading,
    TheComicList,
  },
  props: {
    selector: String
  }
}
</script>
