<template>
  <div class="flex flex-col h-full">
    <LayoutHeader :title="template?.name || 'Template'" />

    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="text-center py-12 text-neutral-500">
        Carregando...
      </div>

      <div v-else-if="template" class="max-w-4xl mx-auto space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-neutral-900">
              {{ template.name }}
            </h2>
            <p class="text-sm text-neutral-500">
              {{ template.url_pattern || 'Sem padrão de URL' }}
            </p>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-secondary" @click="navigateTo('/templates')">
              Voltar
            </button>
            <button class="btn btn-primary" @click="saveTemplate">
              Salvar
            </button>
          </div>
        </div>

        <!-- Template Info -->
        <div class="card p-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-neutral-700 mb-1">
                Nome
              </label>
              <input
                v-model="editedTemplate.name"
                type="text"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-neutral-700 mb-1">
                Padrão de URL
              </label>
              <input
                v-model="editedTemplate.url_pattern"
                type="text"
                class="input"
                placeholder="https://example.com/*"
              />
            </div>
          </div>
        </div>

        <!-- Selectors -->
        <div class="card">
          <div class="p-4 border-b border-neutral-200 flex justify-between items-center">
            <h3 class="font-semibold text-neutral-900">
              Campos ({{ editedTemplate.selectors.length }})
            </h3>
            <button class="btn btn-secondary text-sm" @click="addSelector">
              + Adicionar Campo
            </button>
          </div>

          <div class="divide-y divide-neutral-100">
            <div
              v-for="(selector, index) in editedTemplate.selectors"
              :key="index"
              class="p-4"
            >
              <div class="grid grid-cols-12 gap-4 items-end">
                <div class="col-span-3">
                  <label class="block text-xs font-medium text-neutral-500 mb-1">
                    Nome
                  </label>
                  <input
                    v-model="selector.name"
                    type="text"
                    class="input"
                    placeholder="titulo"
                  />
                </div>
                <div class="col-span-4">
                  <label class="block text-xs font-medium text-neutral-500 mb-1">
                    Selector CSS
                  </label>
                  <input
                    v-model="selector.selector"
                    type="text"
                    class="input"
                    placeholder="h1.title"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-neutral-500 mb-1">
                    Tipo
                  </label>
                  <select v-model="selector.type" class="input">
                    <option value="text">Texto</option>
                    <option value="html">HTML</option>
                    <option value="attribute">Atributo</option>
                    <option value="list">Lista</option>
                  </select>
                </div>
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-neutral-500 mb-1">
                    Atributo
                  </label>
                  <input
                    v-model="selector.attribute"
                    type="text"
                    class="input"
                    placeholder="href"
                    :disabled="selector.type !== 'attribute'"
                  />
                </div>
                <div class="col-span-1">
                  <button
                    class="btn btn-ghost text-red-500 w-full"
                    @click="removeSelector(index)"
                  >
                    X
                  </button>
                </div>
              </div>
            </div>

            <div
              v-if="editedTemplate.selectors.length === 0"
              class="p-8 text-center text-neutral-500"
            >
              Nenhum campo definido. Use a extensão do browser ou adicione manualmente.
            </div>
          </div>
        </div>

        <!-- Test Section -->
        <div class="card p-4">
          <h3 class="font-semibold text-neutral-900 mb-4">Testar Template</h3>
          <div class="flex gap-4">
            <input
              v-model="testUrl"
              type="url"
              class="input flex-1"
              placeholder="https://example.com/page"
            />
            <button
              class="btn btn-primary"
              :disabled="!testUrl || testing"
              @click="runTest"
            >
              {{ testing ? 'Testando...' : 'Testar' }}
            </button>
          </div>

          <!-- Test Result -->
          <div v-if="testResult" class="mt-4 p-4 bg-neutral-50 rounded-lg">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm font-medium text-neutral-700">Resultado</span>
              <span class="text-xs text-neutral-500">
                {{ testResult.duration_ms }}ms
              </span>
            </div>
            <pre class="text-sm text-neutral-800 overflow-auto">{{ JSON.stringify(testResult.data, null, 2) }}</pre>
          </div>

          <div v-if="testError" class="mt-4 p-4 bg-red-50 rounded-lg text-red-700 text-sm">
            {{ testError }}
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import type { SelectorField, Template } from '~/composables/useTemplates'

const route = useRoute()
const api = useApi()
const { updateTemplate, testTemplate } = useTemplates()

const templateId = Number(route.params.id)

const template = ref<Template | null>(null)
const editedTemplate = ref({
  name: '',
  url_pattern: '',
  selectors: [] as SelectorField[],
})
const loading = ref(true)

const testUrl = ref('')
const testing = ref(false)
const testResult = ref<{ data: Record<string, unknown>; duration_ms: number } | null>(null)
const testError = ref<string | null>(null)

const fetchTemplate = async () => {
  loading.value = true
  try {
    template.value = await api.get<Template>(`/templates/${templateId}`)
    editedTemplate.value = {
      name: template.value.name,
      url_pattern: template.value.url_pattern || '',
      selectors: [...template.value.selectors],
    }
  } catch (error) {
    console.error('Failed to fetch template:', error)
  } finally {
    loading.value = false
  }
}

const addSelector = () => {
  editedTemplate.value.selectors.push({
    name: '',
    selector: '',
    type: 'text',
    attribute: undefined,
  })
}

const removeSelector = (index: number) => {
  editedTemplate.value.selectors.splice(index, 1)
}

const saveTemplate = async () => {
  try {
    await updateTemplate(templateId, {
      name: editedTemplate.value.name,
      url_pattern: editedTemplate.value.url_pattern || null,
      selectors: editedTemplate.value.selectors,
    })
    alert('Template salvo!')
  } catch (error) {
    console.error('Failed to save template:', error)
    alert('Erro ao salvar template')
  }
}

const runTest = async () => {
  testing.value = true
  testResult.value = null
  testError.value = null

  try {
    // First save current selectors
    await saveTemplate()
    // Then test
    testResult.value = await testTemplate(templateId, testUrl.value)
  } catch (error) {
    testError.value = error instanceof Error ? error.message : 'Erro ao testar'
  } finally {
    testing.value = false
  }
}

onMounted(fetchTemplate)
</script>
