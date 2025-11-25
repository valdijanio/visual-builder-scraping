<template>
  <aside class="w-64 bg-white border-r border-neutral-200 flex flex-col h-screen">
    <!-- Logo -->
    <div class="p-4 border-b border-neutral-200">
      <h1 class="text-lg font-semibold text-neutral-900">Visual Builder</h1>
      <p class="text-xs text-neutral-500">Web Scraping</p>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-4 space-y-1">
      <NuxtLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="[
          isActive(item.path)
            ? 'bg-primary-50 text-primary-600'
            : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900',
        ]"
      >
        <span class="text-lg">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <!-- Footer -->
    <div class="p-4 border-t border-neutral-200">
      <div class="text-xs text-neutral-400">v1.0.0</div>
    </div>
  </aside>
</template>

<script setup lang="ts">
const route = useRoute()

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/templates', label: 'Templates', icon: '📄' },
  { path: '/schedules', label: 'Agendamentos', icon: '🕐' },
  { path: '/jobs', label: 'Jobs', icon: '⚡' },
  { path: '/results', label: 'Resultados', icon: '📋' },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>
