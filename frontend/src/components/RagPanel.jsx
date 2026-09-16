import { useState } from 'react'

const RAG_API_URL = import.meta.env.VITE_RAG_API_URL ?? 'http://127.0.0.1:8000'

const EXAMPLE_QUERIES = [
  'What is the ISA air density at 10 km altitude?',
  'What proportional navigation gain should I use?',
  'How heavy is the interceptor at launch?',
]

export function RagPanel() {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const runQuery = async (text) => {
    const trimmed = text.trim()
    if (!trimmed) return
    setStatus('loading')
    setError(null)
    try {
      const response = await fetch(`${RAG_API_URL}/ground-spec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed }),
      })
      const body = await response.json().catch(() => null)
      if (!response.ok) {
        throw new Error(body?.detail ?? `Request failed (${response.status}).`)
      }
      setResult(body)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="replay-screen rag-screen" aria-labelledby="rag-title">
      <div className="replay-inner">
        <div className="replay-intro">
          <span className="panel-kicker" id="rag-title">
            SPEC GROUNDING
          </span>
          <p>
            Ask a natural-language question about an aerospace or guidance
            parameter. The <code>aero-spec-rag</code> service retrieves the
            relevant corpus passage, checks the value against a plausibility
            table, and returns a cited, structured answer — never a guess.
          </p>
          <span className="source-chip">{RAG_API_URL}</span>
        </div>

        <form
          className="rag-form"
          onSubmit={(event) => {
            event.preventDefault()
            runQuery(query)
          }}
        >
          <input
            type="text"
            className="rag-input"
            placeholder="e.g. What is the ISA air density at 10 km altitude?"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Spec question"
          />
          <button type="submit" disabled={status === 'loading' || !query.trim()}>
            {status === 'loading' ? 'ASKING…' : 'ASK'}
          </button>
        </form>

        <div className="rag-examples">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              className="rag-example-chip"
              onClick={() => {
                setQuery(example)
                runQuery(example)
              }}
              disabled={status === 'loading'}
            >
              {example}
            </button>
          ))}
        </div>

        {status === 'error' && (
          <div className="rag-result is-error">
            <span className="session-outcome is-miss">UNAVAILABLE</span>
            <p>
              {error} Start the backend with{' '}
              <code>uvicorn src.api:app --reload --port 8000</code> from{' '}
              <code>aero-spec-rag/</code>.
            </p>
          </div>
        )}

        {status === 'done' && result && (
          <div className="rag-result">
            <div className="rag-result-head">
              <span
                className={
                  result.verified ? 'session-outcome' : 'session-outcome is-miss'
                }
              >
                {result.verified ? 'VERIFIED' : 'UNVERIFIED'}
              </span>
              {result.quantity && (
                <span className="source-chip">{result.quantity}</span>
              )}
              {typeof result.confidence === 'number' && (
                <span className="source-chip">
                  confidence {result.confidence.toFixed(2)}
                </span>
              )}
            </div>

            <p className="rag-answer">{result.answer}</p>

            {result.value !== null && result.value !== undefined && (
              <div className="rag-fact-grid">
                <div>
                  <span className="session-detail">VALUE</span>
                  <span className="session-id">
                    {result.value} {result.unit}
                  </span>
                </div>
                <div>
                  <span className="session-detail">SOURCE</span>
                  <span className="session-id">{result.source_doc}</span>
                </div>
              </div>
            )}

            {result.flags?.length > 0 && (
              <div className="rag-flags">
                {result.flags.map((flag) => (
                  <span key={flag.code} className="source-chip">
                    ⚠ {flag.message}
                  </span>
                ))}
              </div>
            )}

            {result.citations?.length > 0 && (
              <div className="session-list">
                {result.citations.map((citation) => (
                  <div key={citation.source_doc + citation.chunk_index} className="session-row rag-citation">
                    <span className="session-copy">
                      <span className="session-id">{citation.title}</span>
                      <span className="session-detail">{citation.snippet}</span>
                    </span>
                    <span className="session-miss">
                      {citation.retrieval_score?.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {result.disclaimer && (
              <p className="rag-disclaimer">{result.disclaimer}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
