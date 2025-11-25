<template>
  <div class="flex flex-col h-full">
    <LayoutHeader title="Jobs" />

    <main class="flex-1 overflow-auto p-6">
      <!-- Actions -->
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-lg font-semibold text-neutral-900">
          Jobs em Memória
        </h3>
        <button class="btn btn-secondary" @click="fetchJobs">
          Atualizar
        </button>
      </div>

      <!-- Jobs Table -->
      <div class="card overflow-hidden">
        <table class="w-full">
          <thead class="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">ID</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">URL</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Template</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Criado</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-neutral-100">
            <tr
              v-for="job in jobs"
              :key="job.id"
              class="hover:bg-neutral-50"
            >
              <td class="p-4 font-mono text-sm text-neutral-600">
                {{ job.id.slice(0, 8) }}...
              </td>
              <td class="p-4 text-neutral-600 truncate max-w-xs">{{ job.url }}</td>
              <td class="p-4 text-neutral-600">{{ job.template_id }}</td>
              <td class="p-4 text-neutral-500 text-sm">
                {{ formatDate(job.created_at) }}
              </td>
              <td class="p-4">
                <span
                  class="badge"
                  :class="getStatusClass(job.status)"
                >
                  {{ job.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div
          v-if="jobs.length === 0 && !loading"
          class="p-12 text-center text-neutral-500"
        >
          Nenhum job em execução
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
const api = useApi()

interface Job {
  id: string
  template_id: number
  url: string
  status: string
  created_at: string
}

const jobs = ref<Job[]>([])
const loading = ref(false)

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('pt-BR')
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'success':
      return 'badge-success'
    case 'failed':
      return 'badge-error'
    case 'running':
      return 'badge-info'
    default:
      return 'badge-warning'
  }
}

const fetchJobs = async () => {
  loading.value = true
  try {
    jobs.value = await api.get<Job[]>('/jobs')
  } catch (error) {
    console.error('Failed to fetch jobs:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchJobs()
  // Auto-refresh every 5 seconds
  setInterval(fetchJobs, 5000)
})
</script>
