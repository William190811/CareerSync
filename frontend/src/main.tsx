import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './style.css'

class DashboardErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null }

  static getDerivedStateFromError(error: Error) { return { error } }

  componentDidCatch(error: Error) { console.error('CareerSync dashboard render failed', error) }

  render() {
    if (this.state.error) return <main className="render-error" role="alert">
      <h1>CareerSync could not finish loading</h1>
      <p>The dashboard encountered a display error. Refresh the page to try again.</p>
      <details><summary>Technical details</summary><code>{this.state.error.message}</code></details>
      <button className="refresh-button" onClick={() => window.location.reload()}>Refresh dashboard</button>
    </main>
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><DashboardErrorBoundary><App /></DashboardErrorBoundary></React.StrictMode>)
