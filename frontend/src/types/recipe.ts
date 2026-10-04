export interface Photo {
  url: string
  author: string
  license: string
}

export interface RecipeSummary {
  slug: string
  name: string
  summary: string
  cuisine: string
  country: string
  category: string
  diets: string[]
  difficulty: string | null
  servings: number | null
  total_minutes: number | null
  protein_g: number | null
  calories: number | null
  photo: Photo | null
  available_ingredients?: string[]
  missing_ingredients?: string[]
  pantry_coverage?: number
  protein_difference_g?: number
  reasons?: string[]
  corpus?: 'unitools' | 'recipe1m'
}

export interface RecipeDetail extends RecipeSummary {
  ingredients: Array<{
    id: string
    name: string
    quantity: number | null
    unit: string
    note: string | null
  }>
  steps: Array<{ text: string; minutes: number | null }>
  nutrition: { protein: number; calories: number; fat: number; carbs: number | null } | null
  nutrition_basis?: 'per_100g' | null
  source: { attribution: string; homepage: string; license: string; licenseUrl: string }
}

export interface SearchResponse {
  parsed_pantry: {
    display_terms: string[]
    recognized: string[]
    deterministic: string[]
    refined: string[]
    core: string[]
    basics: string[]
    unresolved: string[]
    mode: 'deterministic' | 'locally_refined' | 'deterministic_fallback'
    model_status: {
      available: boolean
      model: string
      reason: 'not_needed' | 'ready' | 'service_unavailable' | 'model_missing' | 'timeout' | 'invalid_output'
    }
  }
  results: RecipeSummary[]
  total_eligible: number
}
