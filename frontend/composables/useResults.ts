export interface Result {
  id: number
  template_id: number | null
  schedule_id: number | null
  url: string
  status: string
  data: Record<string, unknown> | null
  error: string | null
  duration_ms: number | null
  extracted_at: string
}

export interface ResultsResponse {
  items: Result[]
  total: number
  page: number
  page_size: number
}

export const useResults = () => {
  const api = useApi()
  const results = useState<Result[]>('results', () => [])
  const total = useState<number>('results-total', () => 0)
  const page = useState<number>('results-page', () => 1)
  const pageSize = useState<number>('results-page-size', () => 20)
  const loading = useState<boolean>('results-loading', () => false)
  const error = useState<string | null>('results-error', () => null)

  const fetchResults = async (filters?: {
    template_id?: number
    schedule_id?: number
    status?: string
    page?: number
    page_size?: number
  }) => {
    loading.value = true
    error.value = null

    const params = new URLSearchParams()
    if (filters?.template_id) params.set('template_id', String(filters.template_id))
    if (filters?.schedule_id) params.set('schedule_id', String(filters.schedule_id))
    if (filters?.status) params.set('status', filters.status)
    params.set('page', String(filters?.page || page.value))
    params.set('page_size', String(filters?.page_size || pageSize.value))

    try {
      const response = await api.get<ResultsResponse>(`/results?${params}`)
      results.value = response.items
      total.value = response.total
      page.value = response.page
      pageSize.value = response.page_size
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch results'
    } finally {
      loading.value = false
    }
  }

  const deleteResult = async (id: number) => {
    await api.delete(`/results/${id}`)
    results.value = results.value.filter((r) => r.id !== id)
    total.value--
  }

  return {
    results,
    total,
    page,
    pageSize,
    loading,
    error,
    fetchResults,
    deleteResult,
  }
}
