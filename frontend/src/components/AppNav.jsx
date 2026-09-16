export const SCREENS = [
  { id: 'hud', code: 'HUD', label: 'Live', title: 'Live engagement' },
  { id: 'setup', code: 'SET', label: 'Setup', title: 'Scenario setup' },
  { id: 'trials', code: 'TRL', label: 'Trials', title: 'All trials overlay' },
  { id: 'train', code: 'TRN', label: 'Training', title: 'Training' },
  { id: 'replay', code: 'RPL', label: 'Replay', title: 'Session replay' },
  { id: 'spec', code: 'RAG', label: 'Spec RAG', title: 'Ask the spec-grounding RAG' },
]

export function AppNav({ screen, onSelect }) {
  return (
    <nav className="app-rail" aria-label="Viewer screens">
      <div className="rail-mark" aria-hidden="true" />
      {SCREENS.map((item) => {
        const active = item.id === screen
        return (
          <button
            key={item.id}
            type="button"
            title={item.title}
            aria-current={active ? 'page' : undefined}
            className={active ? 'rail-btn is-active' : 'rail-btn'}
            onClick={() => onSelect(item.id)}
          >
            <span className="rail-code">{item.code}</span>
            <span className="rail-label">{item.label}</span>
          </button>
        )
      })}
      <div className="rail-spacer" />
      <span className="rail-dof">3-DOF</span>
    </nav>
  )
}
