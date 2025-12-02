<template>
  <div class="app-container">
    <Chat />
  </div>
</template>

<script setup>
import Chat from './components/Chat.vue'
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
