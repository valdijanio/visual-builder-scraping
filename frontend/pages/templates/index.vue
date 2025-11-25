<template>
  <div class="flex flex-col h-full">
    <LayoutHeader title="Templates" />

    <main class="flex-1 overflow-auto p-6">
      <!-- Actions -->
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-lg font-semibold text-neutral-900">
          {{ templates.length }} templates
        </h3>
        <button class="btn btn-primary" @click="showCreateModal = true">
          + Novo Template
        </button>
      </div>

      <!-- Templates Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="template in templates"
          :key="template.id"
          class="card p-4 hover:shadow-soft-md transition-shadow cursor-pointer"
          @click="navigateTo(`/templates/${template.id}`)"
        >
          <div class="flex justify-between items-start mb-2">
            <h4 class="font-semibold text-neutral-900">{{ template.name }}</h4>
            <span
              class="badge"
              :class="template.active ? 'badge-success' : 'badge-neutral'"
            >
              {{ template.active ? 'Ativo' : 'Inativo' }}
            </span>
          </div>
          <p class="text-sm text-neutral-500 mb-3 truncate">
            {{ template.url_pattern || 'Sem padrão de URL' }}
          </p>
          <div class="flex items-center gap-4 text-sm text-neutral-400">
            <span>{{ template.selectors.length }} campos</span>
            <span>{{ formatDate(template.updated_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-if="templates.length === 0 && !loading"
        class="card p-12 text-center"
      >
        <div class="text-4xl mb-4">📄</div>
        <h3 class="text-lg font-semibold text-neutral-900 mb-2">
          Nenhum template ainda
        </h3>
        <p class="text-neutral-500 mb-4">
          Crie seu primeiro template ou use a extensão do browser
        </p>
        <button class="btn btn-primary" @click="showCreateModal = true">
          Criar Template
        </button>
      </div>

      <!-- Create Modal -->
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCreateModal = false"
      >
        <div class="bg-white rounded-lg shadow-soft-lg w-full max-w-md p-6">
          <h3 class="text-lg font-semibold text-neutral-900 mb-4">
            Novo Template
          </h3>
          <form @submit.prevent="createNewTemplate">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Nome
                </label>
                <input
                  v-model="newTemplate.name"
                  type="text"
                  class="input"
                  placeholder="Ex: Preços Amazon"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Padrão de URL (opcional)
                </label>
                <input
                  v-model="newTemplate.url_pattern"
                  type="text"
                  class="input"
                  placeholder="Ex: https://amazon.com.br/dp/*"
                />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button
                type="button"
                class="btn btn-secondary"
                @click="showCreateModal = false"
              >
                Cancelar
              </button>
              <button type="submit" class="btn btn-primary">
                Criar
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
const { templates, loading, fetchTemplates, createTemplate } = useTemplates()

const showCreateModal = ref(false)
const newTemplate = ref({
  name: '',
  url_pattern: '',
})

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('pt-BR')
}

const createNewTemplate = async () => {
  try {
    const template = await createTemplate({
      name: newTemplate.value.name,
      url_pattern: newTemplate.value.url_pattern || undefined,
      selectors: [],
    })
    showCreateModal.value = false
    newTemplate.value = { name: '', url_pattern: '' }
    navigateTo(`/templates/${template.id}`)
  } catch (error) {
    console.error('Failed to create template:', error)
  }
}

onMounted(fetchTemplates)
</script>
