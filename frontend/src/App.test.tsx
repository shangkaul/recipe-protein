import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import App from './App'

const tofuSummary = {
  slug: 'tofu-bowl', name: 'Tofu bowl', summary: 'A simple tofu bowl.', cuisine: 'Global cuisine',
  country: 'Global', category: 'main', diets: [], difficulty: 'easy', servings: 2,
  total_minutes: 25, protein_g: 18, calories: 420, nutrition_available: true, photo: null, corpus: 'unitools',
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  localStorage.clear()
})

test('opens with meal browsing and a pantry action', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ results: [] }) }))
  render(<App />)
  expect(screen.getByRole('heading', { name: 'What sounds good?' })).toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: /use my pantry/i })[0]).toBeInTheDocument()
  expect(screen.getByLabelText(/avoid ingredients/i)).toBeInTheDocument()
  expect(await screen.findByText('No grounded matches yet')).toBeInTheDocument()
})

test('sends exclusions and explains locally refined pantry terms', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [] }) })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        parsed_pantry: {
          display_terms: ['tomatos', 'rice', 'spices'],
          recognized: ['rice', 'tomato'],
          deterministic: ['rice'],
          refined: ['tomato'],
          core: ['rice', 'tomato'],
          basics: ['spices'],
          unresolved: [],
          mode: 'locally_refined',
          model_status: { available: true, model: 'gemma3:1b', reason: 'ready' },
        },
        results: [],
        total_eligible: 0,
        nutrition_ready_count: 0,
        verified_nutrition_only: false,
      }),
    })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)

  fireEvent.change(screen.getByLabelText('Your ingredients'), { target: { value: 'tomatos, rice, spices' } })
  fireEvent.change(screen.getByLabelText(/avoid ingredients/i), { target: { value: 'chicken, peanuts' } })
  fireEvent.click(screen.getByRole('button', { name: 'Find meals' }))

  expect(await screen.findByText(/understood by Gemma on this device/i)).toBeInTheDocument()
  expect(screen.getByText('tomato')).toBeInTheDocument()
  expect(screen.getByText('basic')).toBeInTheDocument()
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
  const request = JSON.parse(fetchMock.mock.calls[1][1].body)
  expect(request.exclusions).toEqual(['chicken', 'peanuts'])
  expect(request.verified_nutrition_only).toBe(false)
})

test('requests and labels only recipes with verified nutrition', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [tofuSummary] }) })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        parsed_pantry: {
          display_terms: ['tofu'], recognized: ['tofu'], deterministic: ['tofu'], refined: [],
          core: ['tofu'], basics: [], unresolved: [], mode: 'deterministic',
          model_status: { available: true, model: 'gemma3:1b', reason: 'not_needed' },
        },
        results: [tofuSummary], total_eligible: 1, nutrition_ready_count: 1,
        verified_nutrition_only: true,
      }),
    })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)

  fireEvent.change(screen.getByLabelText('Your ingredients'), { target: { value: 'tofu' } })
  fireEvent.click(screen.getByLabelText(/verified nutrition only/i))
  fireEvent.click(screen.getByRole('button', { name: 'Find meals' }))

  expect(await screen.findByText(/every result has verified nutrition/i)).toBeInTheDocument()
  expect(screen.getByText('Verified nutrition')).toBeInTheDocument()
  const request = JSON.parse(fetchMock.mock.calls[1][1].body)
  expect(request.verified_nutrition_only).toBe(true)
})

test('explains unavailable adaptation before asking for servings', async () => {
  localStorage.setItem('protein-pantry:pantry', 'pasta')
  const unsupported = { ...tofuSummary, slug: 'local-pasta', name: 'Local pasta', corpus: 'recipe1m', servings: null, protein_g: null, calories: null, nutrition_available: false }
  const detail = {
    ...unsupported,
    ingredients: [{ id: 'pasta', name: 'Pasta', quantity: null, unit: '', note: null }],
    steps: [{ text: 'Cook the pasta.', minutes: null }], nutrition: null,
    source: { attribution: 'Recipe1M', homepage: 'https://example.com', license: 'Source terms', licenseUrl: 'https://example.com' },
  }
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [unsupported] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => detail }))
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'View Local pasta' }))

  expect(await screen.findByText('Adaptation is unavailable for this recipe.')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /confirm servings/i })).not.toBeInTheDocument()
})

test('guides the user to a serving count the recipe can actually produce', async () => {
  localStorage.setItem('protein-pantry:pantry', 'tofu, rice')
  const batch = {
    ...tofuSummary, slug: 'r1m-batch', name: 'Batch casserole', corpus: 'recipe1m',
    servings: null, protein_g: null, calories: null, nutrition_available: true, minimum_servings: 9,
  }
  const detail = {
    ...batch,
    ingredients: [{ id: 'tofu', name: 'Tofu', quantity: null, unit: '', note: null }],
    steps: [{ text: 'Bake.', minutes: null }], nutrition: null, nutrition_basis: 'per_100g',
    source: { attribution: 'Recipe1M', homepage: 'https://example.com', license: 'Source terms', licenseUrl: 'https://example.com' },
  }
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [batch] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => detail })
    .mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'This recipe only divides into a plausible portion at 9 servings or more', reason: 'servings_too_low', minimum_servings: 9 }),
    })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ servings: 9, nutrition: { protein: 12, calories: 300, fat: 8, carbs: null }, basis: 'user_confirmed_servings', source: 'Recipe1M' }) })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'View Batch casserole' }))
  fireEvent.change(await screen.findByLabelText('How many servings will this recipe make?'), { target: { value: '4' } })
  fireEvent.click(screen.getByRole('button', { name: 'Confirm servings' }))

  await waitFor(() => expect(screen.getByLabelText('How many servings will this recipe make?')).toHaveValue(9))
  expect(screen.getByText(/only divides into a plausible portion at 9 servings or more/i)).toBeInTheDocument()
})

test('closes the recipe dialog with Escape and restores focus', async () => {
  const detail = {
    ...tofuSummary,
    ingredients: [{ id: 'tofu', name: 'Tofu', quantity: 200, unit: 'g', note: null }],
    steps: [{ text: 'Cook the tofu.', minutes: null }],
    nutrition: { protein: 18, calories: 420, fat: 12, carbs: 55 },
    source: { attribution: 'Test recipes', homepage: 'https://example.com', license: 'Test', licenseUrl: 'https://example.com' },
  }
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [tofuSummary] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => detail }))
  render(<App />)
  const trigger = await screen.findByRole('button', { name: 'View Tofu bowl' })
  fireEvent.click(trigger)
  const dialog = await screen.findByRole('dialog')
  fireEvent.keyDown(dialog, { key: 'Escape' })

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  await waitFor(() => expect(trigger).toHaveFocus())
})

test('keeps current meals visible while pantry search is running', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
  const pendingSearch = new Promise(() => undefined)
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [tofuSummary] }) })
    .mockReturnValueOnce(pendingSearch)
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  expect(await screen.findByRole('button', { name: 'View Tofu bowl' })).toBeInTheDocument()
  fireEvent.change(screen.getByLabelText('Your ingredients'), { target: { value: 'tofu' } })
  fireEvent.click(screen.getByRole('button', { name: 'Find meals' }))
  expect(screen.getByText('Finding meals that fit your pantry…')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'View Tofu bowl' })).toBeInTheDocument()
})

test('shows a deterministic original-versus-adapted comparison', async () => {
  localStorage.setItem('protein-pantry:pantry', 'tofu, rice')
  const detail = {
    ...tofuSummary,
    ingredients: [{ id: 'tofu', name: 'Firm tofu', quantity: 200, unit: 'g', note: null }],
    steps: [{ text: 'Brown the tofu.', minutes: null }],
    nutrition: { protein: 18, calories: 420, fat: 12, carbs: 55 },
    source: { attribution: 'Test recipes', homepage: 'https://example.com', license: 'Test', licenseUrl: 'https://example.com' },
  }
  const adapted = {
    title: 'Protein-forward tofu bowl', source_slug: 'tofu-bowl', servings: 2,
    changes: [{ action: 'increase', ingredient_id: 'tofu', name: 'Firm tofu', quantity_g: 100, reason: 'Use more pantry tofu', fdc_id: 172448 }],
    instruction_notes: ['Brown the additional tofu in the same pan.'],
    original_nutrition: detail.nutrition,
    nutrition_delta: { protein: 4.5, calories: 39, fat: 2.1 },
    adapted_nutrition: { protein: 22.5, calories: 459, fat: 14.1, carbs: 55 },
    protein_difference_g: -7.5,
    nutrition_source: { name: 'USDA FoodData Central', homepage: 'https://fdc.nal.usda.gov', license: 'Public domain', basis: 'per 100 g edible portion' },
    model: 'gemma-test',
  }
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [tofuSummary] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => detail })
    .mockResolvedValueOnce({ ok: true, json: async () => adapted })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'View Tofu bowl' }))
  fireEvent.click(await screen.findByRole('button', { name: /adapt using my pantry/i }))
  expect(await screen.findByRole('heading', { name: 'Protein-forward tofu bowl' })).toBeInTheDocument()
  expect(screen.getByText('Increase Firm tofu by 100g')).toBeInTheDocument()
  expect(screen.getByText(/USDA FoodData Central/)).toBeInTheDocument()
})
