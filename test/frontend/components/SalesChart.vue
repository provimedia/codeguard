<template>
  <figure class="sales-chart">
    <!-- rendered bars -->
    <div v-for="(v, i) in series" :key="i" class="bar" :style="{ height: v + 'px' }" />
  </figure>
</template>

<script setup>
// NOVEL LIVE_TRAP (vue-dynamic-is): this SFC is reachable ONLY through
// <component :is="chartType"> where chartType === 'SalesChart' at runtime.
// There is no <SalesChart/> tag and no import of it anywhere.
defineProps({ series: { type: Array, default: () => [] } });
</script>
