export interface SelectorField {
  name: string
  selector: string
  type: 'text' | 'html' | 'attribute' | 'list'
  attribute?: string
}

export interface Template {
  id: number
  name: string
  url_pattern: string | null
  selectors: SelectorField[]
  config: Record<string, unknown>
  active: boolean
  created_at: string
  updated_at: string
}

export const useTemplates = () => {
  const api = useApi()
  const templates = useState<Template[]>('templates', () => [])
  const loading = useState<boolean>('templates-loading', () => false)
  const error = useState<string | null>('templates-error', () => null)

  const fetchTemplates = async () => {
    loading.value = true
    error.value = null
    try {
      templates.value = await api.get<Template[]>('/templates')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch templates'
    } finally {
      loading.value = false
    }
  }

  const createTemplate = async (data: {
    name: string
    url_pattern?: string
    selectors: SelectorField[]
  }) => {
    const template = await api.post<Template>('/templates', data)
    templates.value.unshift(template)
    return template
  }

  const updateTemplate = async (id: number, data: Partial<Template>) => {
    const template = await api.put<Template>(`/templates/${id}`, data)
    const index = templates.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      templates.value[index] = template
    }
    return template
  }

  const deleteTemplate = async (id: number) => {
    await api.delete(`/templates/${id}`)
    templates.value = templates.value.filter((t) => t.id !== id)
  }

  const testTemplate = async (id: number, url: string) => {
    return api.post<{ url: string; data: Record<string, unknown>; duration_ms: number }>(
      `/templates/${id}/test`,
      { url }
    )
  }

  return {
    templates,
    loading,
    error,
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    testTemplate,
  }
}
