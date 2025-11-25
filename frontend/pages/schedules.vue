<template>
  <div class="flex flex-col h-full">
    <LayoutHeader title="Agendamentos" />

    <main class="flex-1 overflow-auto p-6">
      <!-- Actions -->
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-lg font-semibold text-neutral-900">
          {{ schedules.length }} agendamentos
        </h3>
        <button class="btn btn-primary" @click="showCreateModal = true">
          + Novo Agendamento
        </button>
      </div>

      <!-- Schedules Table -->
      <div class="card overflow-hidden">
        <table class="w-full">
          <thead class="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Nome</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">URL</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Frequência</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Última Execução</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Status</th>
              <th class="text-left p-4 text-sm font-medium text-neutral-600">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-neutral-100">
            <tr
              v-for="schedule in schedules"
              :key="schedule.id"
              class="hover:bg-neutral-50"
            >
              <td class="p-4 font-medium text-neutral-900">{{ schedule.name }}</td>
              <td class="p-4 text-neutral-600 truncate max-w-xs">{{ schedule.url }}</td>
              <td class="p-4 text-neutral-600">
                {{ schedule.cron_expression || `A cada ${schedule.interval_minutes} min` }}
              </td>
              <td class="p-4 text-neutral-500 text-sm">
                {{ schedule.last_run_at ? formatDate(schedule.last_run_at) : '-' }}
              </td>
              <td class="p-4">
                <span
                  class="badge"
                  :class="schedule.is_enabled ? 'badge-success' : 'badge-neutral'"
                >
                  {{ schedule.is_enabled ? 'Ativo' : 'Pausado' }}
                </span>
              </td>
              <td class="p-4">
                <div class="flex gap-2">
                  <button
                    class="btn btn-ghost text-sm"
                    @click="runNow(schedule.id)"
                  >
                    Executar
                  </button>
                  <button
                    class="btn btn-ghost text-sm"
                    @click="toggleSchedule(schedule)"
                  >
                    {{ schedule.is_enabled ? 'Pausar' : 'Ativar' }}
                  </button>
                  <button
                    class="btn btn-ghost text-sm text-red-500"
                    @click="confirmDelete(schedule.id)"
                  >
                    Excluir
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div
          v-if="schedules.length === 0 && !loading"
          class="p-12 text-center text-neutral-500"
        >
          Nenhum agendamento configurado
        </div>
      </div>

      <!-- Create Modal -->
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCreateModal = false"
      >
        <div class="bg-white rounded-lg shadow-soft-lg w-full max-w-lg p-6">
          <h3 class="text-lg font-semibold text-neutral-900 mb-4">
            Novo Agendamento
          </h3>
          <form @submit.prevent="createNewSchedule">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Template
                </label>
                <select v-model="newSchedule.template_id" class="input" required>
                  <option value="">Selecione...</option>
                  <option
                    v-for="t in templates"
                    :key="t.id"
                    :value="t.id"
                  >
                    {{ t.name }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Nome
                </label>
                <input
                  v-model="newSchedule.name"
                  type="text"
                  class="input"
                  placeholder="Verificar preços diário"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  URL
                </label>
                <input
                  v-model="newSchedule.url"
                  type="url"
                  class="input"
                  placeholder="https://example.com/page"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Tipo de Agendamento
                </label>
                <select v-model="scheduleType" class="input">
                  <option value="interval">Intervalo</option>
                  <option value="cron">Cron Expression</option>
                </select>
              </div>
              <div v-if="scheduleType === 'interval'">
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Intervalo (minutos)
                </label>
                <input
                  v-model.number="newSchedule.interval_minutes"
                  type="number"
                  class="input"
                  min="1"
                  placeholder="60"
                />
              </div>
              <div v-else>
                <label class="block text-sm font-medium text-neutral-700 mb-1">
                  Cron Expression
                </label>
                <input
                  v-model="newSchedule.cron_expression"
                  type="text"
                  class="input"
                  placeholder="0 9 * * *"
                />
                <p class="text-xs text-neutral-500 mt-1">
                  Ex: "0 9 * * *" = todo dia às 9h, "*/30 * * * *" = a cada 30min
                </p>
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
import type { Schedule } from '~/composables/useSchedules'

const { templates, fetchTemplates } = useTemplates()
const { schedules, loading, fetchSchedules, createSchedule, updateSchedule, deleteSchedule, runSchedule } = useSchedules()

const showCreateModal = ref(false)
const scheduleType = ref<'interval' | 'cron'>('interval')
const newSchedule = ref({
  template_id: '' as number | '',
  name: '',
  url: '',
  cron_expression: '',
  interval_minutes: 60,
})

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('pt-BR')
}

const createNewSchedule = async () => {
  try {
    await createSchedule({
      template_id: Number(newSchedule.value.template_id),
      name: newSchedule.value.name,
      url: newSchedule.value.url,
      cron_expression: scheduleType.value === 'cron' ? newSchedule.value.cron_expression : undefined,
      interval_minutes: scheduleType.value === 'interval' ? newSchedule.value.interval_minutes : undefined,
    })
    showCreateModal.value = false
    newSchedule.value = { template_id: '', name: '', url: '', cron_expression: '', interval_minutes: 60 }
  } catch (error) {
    console.error('Failed to create schedule:', error)
    alert('Erro ao criar agendamento')
  }
}

const toggleSchedule = async (schedule: Schedule) => {
  try {
    await updateSchedule(schedule.id, { is_enabled: !schedule.is_enabled })
  } catch (error) {
    console.error('Failed to toggle schedule:', error)
  }
}

const runNow = async (id: number) => {
  try {
    await runSchedule(id)
    alert('Execução iniciada!')
  } catch (error) {
    console.error('Failed to run schedule:', error)
    alert('Erro ao executar')
  }
}

const confirmDelete = async (id: number) => {
  if (confirm('Tem certeza que deseja excluir este agendamento?')) {
    try {
      await deleteSchedule(id)
    } catch (error) {
      console.error('Failed to delete schedule:', error)
    }
  }
}

onMounted(() => {
  fetchTemplates()
  fetchSchedules()
})
</script>
