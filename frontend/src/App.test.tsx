import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import App from './App'

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
})
