export interface Schedule {
  id: number
  template_id: number
  name: string
  url: string
  cron_expression: string | null
  interval_minutes: number | null
  is_enabled: boolean
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
  updated_at: string
}

export const useSchedules = () => {
  const api = useApi()
  const schedules = useState<Schedule[]>('schedules', () => [])
  const loading = useState<boolean>('schedules-loading', () => false)
  const error = useState<string | null>('schedules-error', () => null)

  const fetchSchedules = async () => {
    loading.value = true
    error.value = null
    try {
      schedules.value = await api.get<Schedule[]>('/schedules')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch schedules'
    } finally {
      loading.value = false
    }
  }

  const createSchedule = async (data: {
    template_id: number
    name: string
    url: string
    cron_expression?: string
    interval_minutes?: number
    is_enabled?: boolean
  }) => {
    const schedule = await api.post<Schedule>('/schedules', data)
    schedules.value.unshift(schedule)
    return schedule
  }

  const updateSchedule = async (id: number, data: Partial<Schedule>) => {
    const schedule = await api.put<Schedule>(`/schedules/${id}`, data)
    const index = schedules.value.findIndex((s) => s.id === id)
    if (index !== -1) {
      schedules.value[index] = schedule
    }
    return schedule
  }

  const deleteSchedule = async (id: number) => {
    await api.delete(`/schedules/${id}`)
    schedules.value = schedules.value.filter((s) => s.id !== id)
  }

  const runSchedule = async (id: number) => {
    return api.post<{ message: string; job_id: string }>(`/schedules/${id}/run`)
  }

  return {
    schedules,
    loading,
    error,
    fetchSchedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    runSchedule,
  }
}
