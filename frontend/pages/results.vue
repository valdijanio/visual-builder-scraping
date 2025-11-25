<template>
  <div class="flex flex-col h-full">
    <LayoutHeader title="Resultados" />

    <main class="flex-1 overflow-auto p-6">
      <!-- Filters -->
      <div class="card p-4 mb-6">
        <div class="flex gap-4 items-end">
          <div class="flex-1">
            <label class="block text-sm font-medium text-neutral-700 mb-1">
              Template
            </label>
            <select v-model="filters.template_id" class="input">
              <option value="">Todos</option>
              <option
                v-for="t in templates"
                :key="t.id"
                :value="t.id"
              >
                {{ t.name }}
              </option>
            </select>
          </div>
          <div class="flex-1">
            <label class="block text-sm font-medium text-neutral-700 mb-1">
              Status
            </label>
            <select v-model="filters.status" class="input">
              <option value="">Todos</option>
              <option value="success">Sucesso</option>
              <option value="failed">Falha</option>
            </select>
          </div>
          <button class="btn btn-primary" @click="applyFilters">
            Filtrar
          </button>
        </div>
      </div>

      <!-- Results Table -->
      <div class="card overflow-hidden">
        <table class="w-full">
          <thead class="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">ID</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">URL</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Status</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Duração</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Data</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-neutral-100">
            <tr
              v-for="result in results"
              :key="result.id"
              class="hover:bg-neutral-50"
            >
              <td class="p-4 text-neutral-600">{{ result.id }}</td>
              <td class="p-4 text-neutral-600 truncate max-w-xs">{{ result.url }}</td>
              <td class="p-4">
                <span
                  class="badge"
                  :class="result.status === 'success' ? 'badge-success' : 'badge-error'"
                >
                  {{ result.status }}
                </span>
              </td>
              <td class="p-4 text-neutral-500 text-sm">
                {{ result.duration_ms ? `${result.duration_ms}ms` : '-' }}
              </td>
              <td class="p-4 text-neutral-500 text-sm">
                {{ formatDate(result.extracted_at) }}
              </td>
              <td class="p-4">
                <div class="flex gap-2">
                  <button
                    class="btn btn-ghost text-sm"
                    @click="viewResult(result)"
                  >
                    Ver
                  </button>
                  <button
                    class="btn btn-ghost text-sm text-red-500"
                    @click="confirmDelete(result.id)"
                  >
                    Excluir
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div
          v-if="results.length === 0 && !loading"
          class="p-12 text-center text-neutral-500"
        >
          Nenhum resultado encontrado
        </div>

        <!-- Pagination -->
        <div
          v-if="total > pageSize"
          class="p-4 border-t border-neutral-200 flex justify-between items-center"
        >
          <span class="text-sm text-neutral-500">
            Mostrando {{ (page - 1) * pageSize + 1 }} - {{ Math.min(page * pageSize, total) }} de {{ total }}
          </span>
          <div class="flex gap-2">
            <button
              class="btn btn-secondary text-sm"
              :disabled="page === 1"
              @click="goToPage(page - 1)"
            >
              Anterior
            </button>
            <button
              class="btn btn-secondary text-sm"
              :disabled="page * pageSize >= total"
              @click="goToPage(page + 1)"
            >
              Próxima
            </button>
          </div>
        </div>
      </div>

      <!-- Result Detail Modal -->
      <div
        v-if="selectedResult"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="selectedResult = null"
      >
        <div class="bg-white rounded-lg shadow-soft-lg w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <div class="p-4 border-b border-neutral-200 flex justify-between items-center">
            <h3 class="font-semibold text-neutral-900">Resultado #{{ selectedResult.id }}</h3>
            <button class="btn btn-ghost" @click="selectedResult = null">X</button>
          </div>
          <div class="p-4 overflow-auto flex-1">
            <div class="mb-4">
              <div class="text-sm text-neutral-500 mb-1">URL</div>
              <div class="text-neutral-900 break-all">{{ selectedResult.url }}</div>
            </div>
            <div class="mb-4">
              <div class="text-sm text-neutral-500 mb-1">Status</div>
              <span
                class="badge"
                :class="selectedResult.status === 'success' ? 'badge-success' : 'badge-error'"
              >
                {{ selectedResult.status }}
              </span>
            </div>
            <div v-if="selectedResult.error" class="mb-4">
              <div class="text-sm text-neutral-500 mb-1">Erro</div>
              <div class="text-red-600 bg-red-50 p-3 rounded-lg">{{ selectedResult.error }}</div>
            </div>
            <div v-if="selectedResult.data">
              <div class="text-sm text-neutral-500 mb-1">Dados Extraídos</div>
              <pre class="bg-neutral-50 p-4 rounded-lg overflow-auto text-sm">{{ JSON.stringify(selectedResult.data, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import type { Result } from '~/composables/useResults'

const { templates, fetchTemplates } = useTemplates()
const { results, total, page, pageSize, loading, fetchResults, deleteResult } = useResults()

const filters = ref({
  template_id: '' as number | '',
  status: '',
})

const selectedResult = ref<Result | null>(null)

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('pt-BR')
}

const applyFilters = () => {
  fetchResults({
    template_id: filters.value.template_id || undefined,
    status: filters.value.status || undefined,
    page: 1,
  })
}

const goToPage = (newPage: number) => {
  fetchResults({
    template_id: filters.value.template_id || undefined,
    status: filters.value.status || undefined,
    page: newPage,
  })
}

const viewResult = (result: Result) => {
  selectedResult.value = result
}

const confirmDelete = async (id: number) => {
  if (confirm('Tem certeza que deseja excluir este resultado?')) {
    try {
      await deleteResult(id)
    } catch (error) {
      console.error('Failed to delete result:', error)
    }
  }
}

onMounted(() => {
  fetchTemplates()
  fetchResults()
})
</script>
