/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { SessionReplayPanel } from './SessionReplayPanel'

afterEach(() => {
  cleanup()
})

describe('SessionReplayPanel', () => {
  it('loads the mock session without a file argument', () => {
    const onReplay = vi.fn()
    render(<SessionReplayPanel onReplay={onReplay} />)

    fireEvent.click(screen.getByRole('button', { name: 'Load mock session' }))

    expect(onReplay).toHaveBeenCalledWith()
    expect(screen.getByText(/mock log/i)).toBeTruthy()
  })

  it('forwards a selected JSON file to the replay loader', () => {
    const onReplay = vi.fn()
    const file = new File(['{}'], 'session.json', { type: 'application/json' })
    render(<SessionReplayPanel onReplay={onReplay} />)

    fireEvent.change(screen.getByLabelText('Load JSON file'), {
      target: { files: [file] },
    })

    expect(onReplay).toHaveBeenCalledWith(file)
  })
})
