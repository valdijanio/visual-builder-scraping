<template>
  <header class="h-14 bg-white border-b border-neutral-200 flex items-center justify-between px-6">
    <div>
      <h2 class="text-lg font-semibold text-neutral-900">{{ title }}</h2>
    </div>

    <div class="flex items-center gap-4">
      <!-- Health Status -->
      <div class="flex items-center gap-2 text-sm">
        <span
          class="w-2 h-2 rounded-full"
          :class="health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'"
        ></span>
        <span class="text-neutral-600">
          {{ health?.workers || 0 }} workers
        </span>
        <span class="text-neutral-400">|</span>
        <span class="text-neutral-600">
          {{ health?.jobs_pending || 0 }} pending
        </span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string
}>()

const api = useApi()

interface HealthResponse {
  status: string
  workers: number
  jobs_pending: number
  jobs_running: number
  schedules_active: number
}

const health = ref<HealthResponse | null>(null)

const fetchHealth = async () => {
  try {
    health.value = await api.get<HealthResponse>('/health')
  } catch {
    health.value = null
  }
}

// Fetch health on mount and every 10 seconds
onMounted(() => {
  fetchHealth()
  setInterval(fetchHealth, 10000)
})
</script>
