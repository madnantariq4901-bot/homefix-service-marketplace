<script setup lang="ts">
import type { Review } from "~/services/reviews.service"

defineProps<{
  review: Review
}>()
</script>

<template>
  <div class="review-card">
    <h3>
      Rating: {{ review.rating }}/5
    </h3>

    <p v-if="review.comment">
      {{ review.comment }}
    </p>

    <p v-else>
      No comment
    </p>

    <small>
      Job ID: {{ review.job_id }}
    </small>
  </div>
</template>

<style scoped>
.review-card {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 10px;
  margin-bottom: 15px;
}
</style>