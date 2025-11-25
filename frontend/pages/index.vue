<template>
  <div class="flex flex-col h-full">
    <LayoutHeader title="Dashboard" />

    <main class="flex-1 overflow-auto p-6">
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="card p-4">
          <div class="text-sm text-neutral-500 mb-1">Templates</div>
          <div class="text-2xl font-semibold text-neutral-900">{{ stats.templates }}</div>
        </div>
        <div class="card p-4">
          <div class="text-sm text-neutral-500 mb-1">Agendamentos Ativos</div>
          <div class="text-2xl font-semibold text-neutral-900">{{ stats.schedules }}</div>
        </div>
        <div class="card p-4">
          <div class="text-sm text-neutral-500 mb-1">Jobs Pendentes</div>
          <div class="text-2xl font-semibold text-neutral-900">{{ stats.jobsPending }}</div>
        </div>
        <div class="card p-4">
          <div class="text-sm text-neutral-500 mb-1">Resultados Hoje</div>
          <div class="text-2xl font-semibold text-neutral-900">{{ stats.resultsToday }}</div>
        </div>
      </div>

      <!-- Recent Results -->
      <div class="card">
        <div class="p-4 border-b border-neutral-200">
          <h3 class="font-semibold text-neutral-900">Resultados Recentes</h3>
        </div>
        <div class="divide-y divide-neutral-100">
          <div
            v-for="result in recentResults"
            :key="result.id"
            class="p-4 flex items-center justify-between"
          >
            <div>
              <div class="font-medium text-neutral-900 truncate max-w-md">
                {{ result.url }}
              </div>
              <div class="text-sm text-neutral-500">
                {{ formatDate(result.extracted_at) }}
              </div>
            </div>
            <span
              class="badge"
              :class="result.status === 'success' ? 'badge-success' : 'badge-error'"
            >
              {{ result.status }}
            </span>
          </div>
          <div v-if="recentResults.length === 0" class="p-8 text-center text-neutral-500">
            Nenhum resultado ainda
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
const api = useApi()

interface HealthResponse {
  status: string
  workers: number
  jobs_pending: number
  jobs_running: number
  schedules_active: number
}

interface Result {
  id: number
  url: string
  status: string
  extracted_at: string
}

const stats = ref({
  templates: 0,
  schedules: 0,
  jobsPending: 0,
  resultsToday: 0,
})

const recentResults = ref<Result[]>([])

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('pt-BR')
}

onMounted(async () => {
  try {
    // Fetch health for jobs info
    const health = await api.get<HealthResponse>('/health')
    stats.value.jobsPending = health.jobs_pending
    stats.value.schedules = health.schedules_active

    // Fetch templates count
    const templates = await api.get<unknown[]>('/templates')
    stats.value.templates = templates.length

    // Fetch recent results
    const results = await api.get<{ items: Result[]; total: number }>('/results?page_size=5')
    recentResults.value = results.items
    stats.value.resultsToday = results.total
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
})
</script>
