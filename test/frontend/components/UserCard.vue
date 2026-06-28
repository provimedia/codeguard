<template>
  <article class="user-card">
    <strong>{{ user.name }}</strong>
    <span>{{ user.email }}</span>
  </article>
</template>

<script setup>
// LIVE_TRAP (vue-global): this SFC is consumed ONLY as <UserCard/> in
// Dashboard.vue, via glob global registration. No JS import names it.
defineProps({ user: { type: Object, required: true } });
</script>
