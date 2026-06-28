<template>
  <section class="dashboard">
    <!-- LIVE_TRAP (vue-global): <UserCard/> is the only reference to UserCard.vue.
         It is globally registered (glob), so there is no import for it here. -->
    <UserCard v-for="u in users" :key="u.id" :user="u" />

    <!-- NOVEL LIVE_TRAP (vue-dynamic-is): the chart component is chosen by a
         STRING at runtime. 'SalesChart' never appears as a tag or an import. -->
    <component :is="chartType" :series="series" />
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { formatCurrency } from '../utils/format.js';

const users = ref([]);
const series = ref([]);

// The component name is resolved from data; here it happens to be 'SalesChart'.
const chartType = ref('SalesChart');

const label = formatCurrency(1999);
</script>
