<template>
  <aside class="sidebar">
    <h2>Menu</h2>

    <nav>
      <NuxtLink to="/dashboard">
        Dashboard
      </NuxtLink>

      <NuxtLink to="/jobs">
        Jobs
      </NuxtLink>

      <NuxtLink to="/providers">
        Providers
      </NuxtLink>

      <NuxtLink to="/categories">
        Categories
      </NuxtLink>

      <NuxtLink to="/quotes">
        Quotes
      </NuxtLink>

      <NuxtLink to="/reviews">
        Reviews
      </NuxtLink>

      <NuxtLink to="/profiles">
        Profile
      </NuxtLink>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  min-height: 100vh;
  padding: 25px 18px;
  border-right: 1px solid #ddd;
}

.sidebar h2 {
  margin-bottom: 25px;
}

.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sidebar a {
  text-decoration: none;
  color: inherit;
}
</style>