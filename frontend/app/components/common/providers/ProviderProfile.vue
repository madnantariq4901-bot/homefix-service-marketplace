<script setup lang="ts">
import type { Provider } from "~/types/provider"

defineProps<{
  provider: Provider
}>()
</script>

<template>
  <div class="profile">
    <h1>Provider Profile</h1>

    <div class="info">
      <p>
        <strong>Provider ID:</strong>
        {{ provider.id }}
      </p>

      <p>
        <strong>User ID:</strong>
        {{ provider.user_id }}
      </p>

      <p>
        <strong>Verified:</strong>
        {{ provider.is_verified ? "Yes" : "No" }}
      </p>

      <p>
        <strong>Completed jobs:</strong>
        {{ provider.completed_job_count }}
      </p>

      <p>
        <strong>Identity documents:</strong>
        {{ provider.identity_documents_submitted ? "Submitted" : "Not submitted" }}
      </p>

      <p>
        <strong>Availability:</strong>
        {{ provider.is_available ? "Available" : "Unavailable" }}
      </p>

      <p>
        <strong>Rating:</strong>
        {{ provider.rating_avg.toFixed(1) }}
      </p>

      <p>
        <strong>Total Reviews:</strong>
        {{ provider.rating_count }}
      </p>
    </div>

    <h2>Skills</h2>

    <div v-if="provider.skills.length">
      <div
        v-for="skill in provider.skills"
        :key="skill.id"
        class="skill"
      >
        <p>
          Category ID: {{ skill.category_id }}
        </p>

        <p>
          Experience:
          {{ skill.years_experience }} years
        </p>
      </div>
    </div>

    <p v-else>
      No skills added yet.
    </p>

    <h2>Location</h2>

    <p v-if="provider.current_lat !== null">
      Latitude: {{ provider.current_lat }}
    </p>

    <p v-if="provider.current_lng !== null">
      Longitude: {{ provider.current_lng }}
    </p>

    <p
      v-if="
        provider.current_lat === null ||
        provider.current_lng === null
      "
    >
      Location not available.
    </p>
  </div>
</template>

<style scoped>
.profile {
  max-width: 700px;
  margin: 40px auto;
  padding: 20px;
}

.info {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 10px;
}

.skill {
  margin-top: 10px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>