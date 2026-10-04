import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import App from './App'

afterEach(() => vi.restoreAllMocks())

test('opens with meal browsing and a pantry action', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ results: [] }) }))
  render(<App />)
  expect(screen.getByRole('heading', { name: 'What sounds good?' })).toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: /use my pantry/i })[0]).toBeInTheDocument()
  expect(await screen.findByText('No grounded matches yet')).toBeInTheDocument()
})
