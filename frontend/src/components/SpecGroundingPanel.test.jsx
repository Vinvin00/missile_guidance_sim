/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SpecGroundingPanel } from './SpecGroundingPanel'

const VERIFIED_RESPONSE = {
  query: 'What drag coefficient should I use for a sphere?',
  quantity: 'drag_coefficient',
  value: 0.47,
  value_low: null,
  value_high: null,
  unit: 'dimensionless',
  source_doc: 'drag-coefficients-by-shape.md',
  confidence: 0.8,
  verified: true,
  answer: 'drag coefficient = 0.47 dimensionless, from drag-coefficients-by-shape.md.',
  context: 'sphere, subcritical Reynolds number',
  plausible_bounds: [0.01, 1.5],
  flags: [
    {
      code: 'illustrative_source',
      severity: 'info',
      message: 'placeholder value',
    },
  ],
  citations: [
    {
      source_doc: 'drag-coefficients-by-shape.md',
      title: 'Typical Drag Coefficient Ranges by Body Shape',
      source_type: 'illustrative',
      chunk_index: 2,
      snippet: 'A smooth sphere shows a striking discontinuity…',
      retrieval_score: 0.46,
    },
  ],
  narration_model: null,
  disclaimer: 'Illustrative corpus. Values are teaching figures, not real specs.',
}

const UNVERIFIED_RESPONSE = {
  query: 'What colour is the interceptor painted?',
  quantity: null,
  value: null,
  value_low: null,
  value_high: null,
  unit: null,
  source_doc: null,
  confidence: 0,
  verified: false,
  answer: 'No grounded value could be extracted from the corpus for this query.',
  context: '',
  plausible_bounds: null,
  flags: [{ code: 'unknown_quantity', severity: 'warning', message: 'no match' }],
  citations: [],
  narration_model: null,
  disclaimer: 'Illustrative corpus. Values are teaching figures, not real specs.',
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

describe('SpecGroundingPanel', () => {
  it('submits the typed query and renders a verified result', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => VERIFIED_RESPONSE,
    })

    render(<SpecGroundingPanel />)

    fireEvent.change(screen.getByLabelText('QUERY'), {
      target: { value: 'What drag coefficient should I use for a sphere?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'ASK' }))

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/ground-spec'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ query: 'What drag coefficient should I use for a sphere?' }),
      }),
    )

    await waitFor(() => expect(screen.getByText('VERIFIED')).toBeTruthy())
    expect(screen.getByText('0.47')).toBeTruthy()
    expect(screen.getAllByText(/drag-coefficients-by-shape\.md/).length).toBeGreaterThan(0)
  })

  it('renders an unverified result without a value or crashing', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => UNVERIFIED_RESPONSE,
    })

    render(<SpecGroundingPanel />)
    fireEvent.change(screen.getByLabelText('QUERY'), {
      target: { value: 'What colour is the interceptor painted?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'ASK' }))

    await waitFor(() => expect(screen.getByText('UNVERIFIED')).toBeTruthy())
    expect(screen.queryByText('0.47')).toBeFalsy()
  })

  it('shows a reachability error when the backend is unavailable', async () => {
    fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    render(<SpecGroundingPanel />)
    fireEvent.change(screen.getByLabelText('QUERY'), {
      target: { value: 'anything' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'ASK' }))

    await waitFor(() => expect(screen.getByText(/Could not reach/i)).toBeTruthy())
  })

  it('fills the query and asks immediately from an example chip', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => VERIFIED_RESPONSE,
    })

    render(<SpecGroundingPanel />)
    fireEvent.click(
      screen.getByRole('button', {
        name: 'What drag coefficient should I use for a sphere?',
      }),
    )

    expect(screen.getByLabelText('QUERY').value).toBe(
      'What drag coefficient should I use for a sphere?',
    )
    await waitFor(() => expect(screen.getByText('VERIFIED')).toBeTruthy())
  })
})
