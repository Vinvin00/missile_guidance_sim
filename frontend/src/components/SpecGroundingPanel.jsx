import { useCallback, useId, useRef, useState } from 'react'

const AERO_RAG_API_URL =
  import.meta.env.VITE_AERO_RAG_API_URL ?? 'http://127.0.0.1:8000'

const EXAMPLE_QUERIES = [
  'What is the ISA air density at 10 km altitude?',
  'What drag coefficient should I use for a sphere?',
  'What proportional navigation gain should I use?',
  'How heavy is the medium-range interceptor at launch?',
]

function formatValue(spec) {
  if (spec.value_low != null && spec.value_high != null) {
    return `${spec.value_low} – ${spec.value_high}`
  }
  if (spec.value != null) return String(spec.value)
  return '—'
}

export function SpecGroundingPanel() {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const inputId = useId()
  const controllerRef = useRef(null)

  const runQuery = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed) return

    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setStatus('loading')
    setErrorMessage('')

    try {
      const response = await fetch(`${AERO_RAG_API_URL}/ground-spec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed }),
        signal: controller.signal,
      })
      if (!response.ok) {
        throw new Error(`Grounding request failed (${response.status}).`)
      }
      const data = await response.json()
      setResult(data)
      setStatus('done')
    } catch (error) {
      if (error.name === 'AbortError') return
      setErrorMessage(
        error.message.includes('fetch')
          ? `Could not reach the grounding service at ${AERO_RAG_API_URL}. Is it running?`
          : error.message,
      )
      setStatus('error')
    }
  }, [])

  const handleSubmit = useCallback(
    (event) => {
      event.preventDefault()
      runQuery(query)
    },
    [query, runQuery],
  )

  const handleExample = useCallback(
    (text) => {
      setQuery(text)
      runQuery(text)
    },
    [runQuery],
  )

  return (
    <div className="spec-screen" aria-labelledby="spec-grounding-title">
      <div className="spec-inner">
        <div className="spec-intro">
          <span className="panel-kicker" id="spec-grounding-title">
            SPEC GROUNDING
          </span>
          <p>
            Ask a question about a guidance or aerospace parameter. The
            answer is retrieved and bounds-checked against a document
            corpus, not generated — every value carries a source citation.
          </p>
          <span className="source-chip">
            aero-spec-rag · illustrative corpus, not real specs
          </span>
        </div>

        <form className="spec-form" onSubmit={handleSubmit}>
          <label htmlFor={inputId} className="spec-form-label">
            QUERY
          </label>
          <div className="spec-form-row">
            <input
              id={inputId}
              type="text"
              value={query}
              placeholder="e.g. What is the ISA air density at 10 km altitude?"
              onChange={(event) => setQuery(event.target.value)}
              autoComplete="off"
            />
            <button type="submit" disabled={status === 'loading' || !query.trim()}>
              {status === 'loading' ? 'ASKING…' : 'ASK'}
            </button>
          </div>
        </form>

        <div className="spec-examples">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              className="spec-example-chip"
              disabled={status === 'loading'}
              onClick={() => handleExample(example)}
            >
              {example}
            </button>
          ))}
        </div>

        {status === 'error' && (
          <div className="spec-result spec-result-error">
            <span className="panel-kicker">ERROR</span>
            <p>{errorMessage}</p>
          </div>
        )}

        {status === 'done' && result && (
          <div className="spec-result">
            <div className="spec-result-head">
              <span
                className={
                  result.verified
                    ? 'spec-verified-badge'
                    : 'spec-verified-badge is-unverified'
                }
              >
                {result.verified ? 'VERIFIED' : 'UNVERIFIED'}
              </span>
              {result.quantity && (
                <span className="spec-quantity">
                  {result.quantity.replaceAll('_', ' ')}
                </span>
              )}
              {result.verified && (
                <span className="spec-confidence">
                  confidence {Math.round(result.confidence * 100)}%
                </span>
              )}
            </div>

            {result.verified && (
              <div className="spec-value-row">
                <span className="spec-value">{formatValue(result)}</span>
                <span className="spec-unit">{result.unit}</span>
              </div>
            )}

            <p className="spec-answer">{result.answer}</p>

            {result.flags?.length > 0 && (
              <div className="spec-flags">
                {result.flags.map((flag) => (
                  <span
                    key={flag.code}
                    className={`spec-flag spec-flag-${flag.severity}`}
                    title={flag.message}
                  >
                    {flag.code.replaceAll('_', ' ')}
                  </span>
                ))}
              </div>
            )}

            {result.citations?.length > 0 && (
              <div className="spec-citations">
                <span className="panel-kicker">SOURCES</span>
                {result.citations.map((citation) => (
                  <div key={`${citation.source_doc}-${citation.chunk_index}`} className="spec-citation">
                    <span className="spec-citation-doc">
                      {citation.source_doc}
                      <span className="spec-citation-type">
                        {citation.source_type}
                      </span>
                    </span>
                    <span className="spec-citation-snippet">
                      {citation.snippet}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <p className="spec-disclaimer">{result.disclaimer}</p>
          </div>
        )}
      </div>
    </div>
  )
}
