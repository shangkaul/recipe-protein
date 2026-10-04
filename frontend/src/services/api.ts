import type { RecipeDetail, RecipeSummary, SearchResponse } from '../types/recipe'

const API_URL = import.meta.env.VITE_API_URL || '/api'

async function getJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.error || 'The local recipe service is unavailable.')
  }
  return response.json()
}

export async function getFeatured(category?: string): Promise<RecipeSummary[]> {
  const query = new URLSearchParams({ limit: '18' })
  if (category && category !== 'all') query.set('category', category)
  const data = await getJson<{ results: RecipeSummary[] }>(`/recipes/featured?${query}`)
  return data.results
}

export async function searchRecipes(payload: {
  text: string
  protein_target_g: number
  preferred_minutes: number | null
  exclusions: string[]
}): Promise<SearchResponse> {
  return getJson('/recipes/search', { method: 'POST', body: JSON.stringify({ ...payload, limit: 24 }) })
}

export async function getRecipe(slug: string): Promise<RecipeDetail> {
  return getJson(`/recipes/${slug}`)
}
